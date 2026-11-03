using System.Diagnostics;
using System.Globalization;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using Azure;
using Azure.Core;
using Azure.Core.Pipeline;
using Azure.Identity;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Models;

return await Experiment.RunAsync(args);

static class Experiment
{
    internal const string Api = "2025-09-01";
    internal const int Top = 5;
    internal const int Records = 6158;
    internal const int MixedRecords = 6183;
    static int FixtureVersion(JsonObject manifest)
    {
        var version = manifest["fixtureVersion"]!.GetValue<int>();
        return version is 1 or 2 ? version : throw new InvalidDataException("Unsupported fixture version.");
    }
    static int IndexedRecords(JsonObject manifest) => FixtureVersion(manifest) == 2 ? MixedRecords : Records;
    static string IndexName(JsonObject manifest) => FixtureVersion(manifest) == 2
        ? "hybrid-pagination-mixed-v2" : "hybrid-pagination-debug";
    static HashSet<string> IdRange(int start, int count) =>
        Enumerable.Range(start, count).Select(i => $"doc-{i:D6}").ToHashSet(StringComparer.Ordinal);
    internal static readonly JsonSerializerOptions Json = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };
    static readonly string[] EnvironmentKeys =
    [
        "AZURE_SUBSCRIPTION_ID", "AZURE_TENANT_ID", "AZURE_RESOURCE_GROUP",
        "AZURE_RESOURCE_GROUP_ID", "AZURE_LOCATION", "AZURE_SEARCH_SERVICE_NAME",
        "AZURE_SEARCH_RESOURCE_ID", "AZURE_SEARCH_ENDPOINT", "AZURE_OPERATOR_OBJECT_ID"
    ];

    public static async Task<int> RunAsync(string[] args)
    {
        var cli = ParseArguments(args);
        var manifestPath = Path.GetFullPath(cli["--manifest"]);
        var manifest = ReadObject(manifestPath);
        var declared = ReadObject(Path.Combine(Path.GetDirectoryName(manifestPath)!, "declared-schema.json"));
        var expectedIds = ValidateFixture(manifest, declared, manifestPath);
        var environment = ReadEnvironment(cli["--env-file"]);
        var runDirectory = Path.TrimEndingDirectorySeparator(Path.GetFullPath(cli["--run-dir"]));
        Directory.CreateDirectory(runDirectory);
        var name = $"dotnet-{cli["--case"]}";
        var reportPath = Path.Combine(runDirectory, name + ".json");
        var observationsPath = Path.Combine(runDirectory, name + ".pages.jsonl");
        var schemaPath = Path.Combine(runDirectory, name + ".schema.json");
        if (File.Exists(reportPath) || File.Exists(observationsPath) || File.Exists(schemaPath))
            throw new IOException("Refusing to overwrite an existing case. Use a new run directory.");
        var report = new CaseReport
        {
            RunId = Path.GetFileName(runDirectory),
            Case = cli["--case"],
            Fixture = manifest,
            Environment = environment,
            Index = new JsonObject
            {
                ["name"] = Text(manifest, "indexName"),
                ["actualSchemaFile"] = name + ".schema.json"
            },
            Query = QueryBody(cli["--case"], manifest),
            ObservationsFile = name + ".pages.jsonl",
            Client = new JsonObject
            {
                ["runtime"] = RuntimeInformation.FrameworkDescription,
                ["sdk"] = PackageVersion(typeof(SearchClient).Assembly),
                ["identity"] = PackageVersion(Assembly.Load("Azure.Identity")),
                ["configuredApi"] = Api,
                ["packages"] = new JsonObject
                {
                    ["Azure.Search.Documents"] = PackageVersion(typeof(SearchClient).Assembly),
                    ["Azure.Identity"] = PackageVersion(Assembly.Load("Azure.Identity"))
                },
                ["retries"] = 0,
                ["observedApis"] = new JsonArray(),
                ["defaults"] = new JsonObject
                {
                    ["queryType"] = new JsonObject { ["value"] = "simple", ["source"] = "documented" },
                    ["searchMode"] = new JsonObject { ["value"] = "any", ["source"] = "documented" },
                    ["vectorFilterMode"] = new JsonObject { ["value"] = "preFilter", ["source"] = "documented" },
                    ["ordering"] = "omitted; relevance and ties are service-defined",
                    ["hybridTextRecall"] = "documented 1000; not explicitly configured or verified"
                }
            }
        };
        // CreateNew protects a case from concurrent invocations, including a failed earlier run.
        using (var initial = new FileStream(reportPath, FileMode.CreateNew, FileAccess.Write, FileShare.Read))
        {
            JsonSerializer.Serialize(initial, report, Json);
            initial.Flush(true);
        }
        using var evidence = new FileStream(observationsPath, FileMode.CreateNew, FileAccess.Write, FileShare.Read);
        using var writer = new StreamWriter(evidence, new UTF8Encoding(false)) { AutoFlush = true };
        var observations = new List<PageObservation>();
        var capture = new CapturePolicy();
        var options = new SearchClientOptions(SearchClientOptions.ServiceVersion.V2025_09_01);
        options.Retry.MaxRetries = 0;
        options.Diagnostics.IsLoggingEnabled = false;
        options.Diagnostics.IsLoggingContentEnabled = false;
        options.AddPolicy(capture, HttpPipelinePosition.PerRetry);
        var credential = new AzureCliCredential(new AzureCliCredentialOptions
        {
            Subscription = environment["AZURE_SUBSCRIPTION_ID"]
        });
        var endpoint = new Uri(environment["AZURE_SEARCH_ENDPOINT"]);
        var search = new SearchClient(endpoint, Text(manifest, "indexName"), credential, options);
        var indexes = new SearchIndexClient(endpoint, credential, options);

        void Save() => WriteReport(reportPath, report);
        void Refresh()
        {
            Summarize(report, observations, expectedIds);
            report.Client["observedApis"] = new JsonArray(observations
                .Select(o => o.ApiVersion).Where(v => v is not null).Distinct()
                .Select(v => (JsonNode?)JsonValue.Create(v)).ToArray());
        }
        int Stop(string reason, string status = "incomplete")
        {
            if (!report.Reasons.Contains(reason)) report.Reasons.Add(reason);
            report.Status = status;
            report.Outcome = "blocked/incomplete";
            report.FinishedAt = DateTimeOffset.UtcNow;
            Refresh();
            Save();
            Console.Error.WriteLine($"{name}: {reason}. Evidence: {reportPath}");
            return 1;
        }

        async Task<PageObservation> Measure(int skip, string phase)
        {
            var observation = new PageObservation
            {
                RunId = report.RunId, Case = report.Case, Phase = phase,
                PageNumber = skip / Top + 1, Skip = skip,
                Advertised = report.Summary.ReportedCount is long count && skip < count
            };
            capture.Reset();
            try
            {
                var request = new SearchOptions { Size = Top, Skip = skip, IncludeTotalCount = true };
                request.Select.Add("id");
                if (report.Case != "vector")
                {
                    request.QueryType = SearchQueryType.Simple;
                    request.SearchMode = SearchMode.Any;
                    request.SearchFields.Add("content");
                }
                if (report.Case != "keyword")
                {
                    request.VectorSearch = new VectorSearchOptions();
                    var vector = new VectorizedQuery(manifest["queryVector"]!.AsArray()
                        .Select(v => v!.GetValue<float>()).ToArray())
                    {
                        KNearestNeighborsCount = 50, Exhaustive = true
                    };
                    vector.Fields.Add("vector");
                    request.VectorSearch.Queries.Add(vector);
                }
                var response = await search.SearchAsync<SearchDocument>(
                    report.Case == "vector" ? null : "maths", request);
                observation.ReportedCount = response.Value.TotalCount;
                var raw = JsonNode.Parse(response.GetRawResponse().Content)!;
                observation.Continuation = raw["@odata.nextLink"] is not null
                    || raw["@search.nextPageParameters"] is not null;
                await using var pages = response.Value.GetResultsAsync().AsPages().GetAsyncEnumerator();
                if (!await pages.MoveNextAsync())
                    throw new InvalidDataException("The SDK did not expose its initial response page.");
                var page = pages.Current;
                observation.Continuation |= !string.IsNullOrEmpty(page.ContinuationToken);
                observation.Ids = page.Values.Select(r => r.Document["id"].ToString()!).ToArray();
                observation.Scores = page.Values.Select(r => r.Score).ToArray();
                observation.RowCount = page.Values.Count;
                observation.CopyCapture(capture);
                if (skip == 0 && phase == "scan")
                {
                    observation.Advertised = observation.ReportedCount > 0;
                    report.Summary.ReportedCount = observation.ReportedCount;
                    report.Summary.ScanBasis = observation.ReportedCount is null ? "vector-k" : "advertised-count";
                    report.Summary.ScanPageCount = observation.ReportedCount is long total
                        ? checked((int)((total + Top - 1) / Top)) : 10;
                    report.Summary.AdvertisedPages = observation.ReportedCount is null
                        ? null : report.Summary.ScanPageCount;
                }
                if (observation.RowCount < Top && observation.Continuation)
                    observation.IncompleteReason = "service-continuation";
                else if (observation.SendCount != 1)
                    observation.IncompleteReason = "search-send-count";
                else if (observation.ApiVersion != Api || observation.Method != "POST"
                    || observation.NormalizedRequest?["skip"]?.GetValue<int>() != skip
                    || !JsonNode.DeepEquals(WithoutSkip(observation.NormalizedRequest), report.Query))
                    observation.IncompleteReason = "effective-request-mismatch";
                else if (observation.RowCount > Top || observation.Ids.Any(id => !expectedIds.Contains(id))
                    || observation.Ids.Distinct().Count() != observation.RowCount)
                    observation.IncompleteReason = "invalid-result";
                Append(observation);
                return observation;
            }
            catch (RequestFailedException error)
            {
                observation.CopyCapture(capture);
                observation.Ids = null;
                observation.Scores = null;
                observation.RowCount = null;
                observation.ReportedCount = null;
                observation.Error = Failure(error);
                Append(observation);
                throw;
            }
        }

        void Append(PageObservation observation)
        {
            observations.Add(observation);
            writer.WriteLine(JsonSerializer.Serialize(observation, Json));
            writer.Flush();
            evidence.Flush(true);
        }

        try
        {
            await ValidateIdentity(environment);
            var actualResponse = await indexes.GetIndexAsync(Text(manifest, "indexName"));
            var actualText = actualResponse.GetRawResponse().Content.ToString();
            using (var actualFile = new FileStream(schemaPath, FileMode.CreateNew, FileAccess.Write))
            using (var actualWriter = new StreamWriter(actualFile, new UTF8Encoding(false)))
                actualWriter.Write(actualText);
            if (!SchemaEquivalent(declared, JsonNode.Parse(actualText)!))
                return Stop("index-schema-mismatch", "blocked");
            report.Summary.IndexCountStart = (await search.GetDocumentCountAsync()).Value;
            Save();
            if (report.Summary.IndexCountStart != IndexedRecords(manifest))
                return Stop("index-count-mismatch", "blocked");
            if (FixtureVersion(manifest) == 2)
                await VerifyPreparedFixture(manifestPath, manifest, environment, search);
            var first = await Measure(0, "scan");
            if (first.IncompleteReason is not null) return Stop(first.IncompleteReason);
            if (first.ReportedCount is null && report.Case != "vector")
                return Stop("initial-count-unavailable");
            for (var page = 1; page < report.Summary.ScanPageCount; page++)
            {
                var observed = await Measure(checked(page * Top), "scan");
                if (observed.IncompleteReason is not null) return Stop(observed.IncompleteReason);
            }
            Refresh();
            var primary = Primary(report, observations).ToArray();
            var lastPopulated = primary.LastOrDefault(o => o.RowCount > 0);
            var firstEmpty = primary.FirstOrDefault(o => o.RowCount == 0);
            var offsets = new SortedSet<int>();
            if (lastPopulated is not null)
            {
                offsets.Add(lastPopulated.Skip);
                offsets.Add(checked(lastPopulated.Skip + Top));
            }
            if (report.Summary.ScanPageCount > 0)
                offsets.Add(checked((report.Summary.ScanPageCount.Value - 1) * Top));
            else offsets.Add(0);
            if (firstEmpty is not null) offsets.Add(firstEmpty.Skip);
            foreach (var skip in offsets)
            {
                var original = observations.FirstOrDefault(o => o.Skip == skip);
                original ??= await Measure(skip, "boundary-probe");
                if (original.IncompleteReason is not null) return Stop(original.IncompleteReason);
                var repeated = await Measure(skip, "boundary-repeat");
                if (repeated.IncompleteReason is not null) return Stop(repeated.IncompleteReason);
                report.Boundaries.Add(new Boundary
                {
                    Skip = skip,
                    ObservationIndexes = [observations.IndexOf(original), observations.IndexOf(repeated)],
                    CountAgreement = original.ReportedCount is null || repeated.ReportedCount is null
                        ? null : original.ReportedCount == repeated.ReportedCount,
                    SizeAgreement = original.RowCount == repeated.RowCount,
                    IdSetAgreement = original.Ids!.ToHashSet().SetEquals(repeated.Ids!),
                    OrderAgreement = original.Ids!.SequenceEqual(repeated.Ids!)
                });
            }
            report.Summary.IndexCountEnd = (await search.GetDocumentCountAsync()).Value;
            Refresh();
            if (report.Summary.IndexCountEnd != IndexedRecords(manifest)) return Stop("index-count-changed");
            if (report.Summary.CountChanged) return Stop("count-drift");
            if (report.Summary.ScanCoverage != 1) return Stop("unfinished-scan");
            if (report.Boundaries.Any(b => b.CountAgreement == false || !b.SizeAgreement || !b.IdSetAgreement))
                return Stop("boundary-instability");
            if (report.Summary.DuplicateIds.Count != 0) return Stop("duplicate-results");
            if (report.Case == "keyword" && report.Summary.BaselineValid != true)
                return Stop("keyword-baseline-invalid");
            if (FixtureVersion(manifest) == 2 && report.Case == "vector" && report.Summary.VectorMembershipValid != true)
                return Stop("vector-membership-failed");
            if (report.Summary.ScanBasis == "vector-k")
            {
                report.Outcome = "not-applicable";
                report.Reasons.Add("count-unavailable");
            }
            else if (report.Summary.ReportedMinusReachable > 0 && report.Summary.EmptyPages > 0)
                report.Outcome = "reproduced";
            else if (report.Summary.ReportedMinusReachable == 0 && report.Summary.EmptyPages == 0)
                report.Outcome = "not-reproduced";
            else return Stop("inconsistent-count-pagination-evidence");
            report.Status = "complete";
            report.FinishedAt = DateTimeOffset.UtcNow;
            Save();
            Console.WriteLine($"{name}: {report.Outcome}; {report.Summary.UniqueReachableIds} unique IDs; {reportPath}");
            return 0;
        }
        catch (RequestFailedException error)
        {
            report.Errors.Add(Failure(error));
            Stop("sdk-request-failed");
            throw;
        }
        catch (AuthenticationFailedException error)
        {
            report.Errors.Add(new JsonObject { ["type"] = error.GetType().Name });
            Stop("authentication-failed", "blocked");
            throw;
        }
        catch (InvalidDataException error)
        {
            report.Reasons.Add(error.Message);
            Stop("invalid-input-or-response", "blocked");
            throw;
        }
    }

    static Dictionary<string, string> ParseArguments(string[] args)
    {
        var keys = new[] { "--case", "--manifest", "--env-file", "--run-dir" };
        var values = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var i = 0; i < args.Length; i += 2)
        {
            if (i + 1 == args.Length || !keys.Contains(args[i]) || string.IsNullOrWhiteSpace(args[i + 1])
                || !values.TryAdd(args[i], args[i + 1]))
                throw new ArgumentException("Require --case keyword|vector|hybrid --manifest PATH --env-file PATH --run-dir PATH.");
        }
        if (values.Count != keys.Length || !new[] { "keyword", "vector", "hybrid" }.Contains(values["--case"]))
            throw new ArgumentException("Require --case keyword|vector|hybrid --manifest PATH --env-file PATH --run-dir PATH.");
        return values;
    }

    static Dictionary<string, string> ReadEnvironment(string path)
    {
        var values = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var line in File.ReadLines(path))
        {
            if (string.IsNullOrWhiteSpace(line) || line.TrimStart().StartsWith('#')) continue;
            var split = line.IndexOf('=');
            if (split < 1 || !values.TryAdd(line[..split], line[(split + 1)..])
                || string.IsNullOrWhiteSpace(line[(split + 1)..]))
                throw new InvalidDataException("Expected generated plain KEY=value environment file.");
        }
        if (!values.Keys.ToHashSet().SetEquals(EnvironmentKeys))
            throw new InvalidDataException("Environment must contain exactly the nine deployment-output keys.");
        foreach (var key in new[] { "AZURE_SUBSCRIPTION_ID", "AZURE_TENANT_ID", "AZURE_OPERATOR_OBJECT_ID" })
            if (!Guid.TryParse(values[key], out _)) throw new InvalidDataException($"Invalid GUID: {key}");
        var service = values["AZURE_SEARCH_SERVICE_NAME"];
        if (service.Length == 0 || service.Any(c => !"abcdefghijklmnopqrstuvwxyz0123456789-".Contains(c)))
            throw new InvalidDataException("Invalid Search service name.");
        var group = $"/subscriptions/{values["AZURE_SUBSCRIPTION_ID"]}/resourceGroups/{values["AZURE_RESOURCE_GROUP"]}";
        var expected = new Dictionary<string, string>
        {
            ["AZURE_RESOURCE_GROUP_ID"] = group,
            ["AZURE_SEARCH_RESOURCE_ID"] = $"{group}/providers/Microsoft.Search/searchServices/{service}",
            ["AZURE_SEARCH_ENDPOINT"] = $"https://{service}.search.windows.net",
            ["AZURE_LOCATION"] = "northeurope"
        };
        if (expected.Any(kv => !string.Equals(values[kv.Key], kv.Value, StringComparison.OrdinalIgnoreCase)))
            throw new InvalidDataException("Environment deployment identities are inconsistent.");
        return values;
    }

    static async Task ValidateIdentity(Dictionary<string, string> environment)
    {
        var az = ResolveAzureCli();
        var info = AzureCliStart(az, "account show --output json");
        using var accountProcess = Process.Start(info)!;
        var outputTask = accountProcess.StandardOutput.ReadToEndAsync();
        var errorTask = accountProcess.StandardError.ReadToEndAsync();
        await accountProcess.WaitForExitAsync();
        var output = await outputTask;
        var stderr = await errorTask;
        if (accountProcess.ExitCode != 0)
            throw new InvalidDataException($"az account show failed ({accountProcess.ExitCode}): {stderr}\n{output}");
        var account = JsonNode.Parse(output)!;
        if (!SameGuid(account["id"]!.GetValue<string>(), environment["AZURE_SUBSCRIPTION_ID"])
            || !SameGuid(account["tenantId"]!.GetValue<string>(), environment["AZURE_TENANT_ID"])
            || account["user"]?["type"]?.GetValue<string>() != "user")
            throw new InvalidDataException("Current Azure CLI subscription/tenant/user does not match setup exports.");
        using var userProcess = Process.Start(AzureCliStart(az, "ad signed-in-user show --query id --output tsv"))!;
        outputTask = userProcess.StandardOutput.ReadToEndAsync();
        errorTask = userProcess.StandardError.ReadToEndAsync();
        await userProcess.WaitForExitAsync();
        output = await outputTask;
        stderr = await errorTask;
        if (userProcess.ExitCode != 0)
            throw new InvalidDataException($"az ad signed-in-user show failed ({userProcess.ExitCode}): {stderr}\n{output}");
        if (!SameGuid(output.Trim(), environment["AZURE_OPERATOR_OBJECT_ID"]))
            throw new InvalidDataException("Current signed-in Azure CLI user differs from the exported setup user.");
    }

    static string ResolveAzureCli()
    {
        var names = OperatingSystem.IsWindows() ? new[] { "az.cmd", "az.exe" } : ["az"];
        foreach (var directory in (System.Environment.GetEnvironmentVariable("PATH") ?? "").Split(Path.PathSeparator))
            foreach (var name in names)
            {
                var candidate = Path.Combine(directory.Trim('"'), name);
                if (File.Exists(candidate)) return candidate;
            }
        foreach (var directory in new[] { "ProgramFiles", "ProgramFiles(x86)" })
        {
            var candidate = Path.Combine(System.Environment.GetEnvironmentVariable(directory) ?? "",
                "Microsoft SDKs", "Azure", "CLI2", "wbin", "az.cmd");
            if (File.Exists(candidate)) return candidate;
        }
        throw new InvalidDataException("Azure CLI is required; run the existing setup notebook.");
    }

    static ProcessStartInfo AzureCliStart(string az, string arguments)
    {
        var windowsCommand = OperatingSystem.IsWindows() && az.EndsWith(".cmd", StringComparison.OrdinalIgnoreCase);
        return new ProcessStartInfo
        {
            FileName = windowsCommand ? System.Environment.GetEnvironmentVariable("ComSpec")! : az,
            Arguments = windowsCommand ? $"/d /s /c \"\"{az}\" {arguments}\"" : arguments,
            RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true
        };
    }

    static bool SameGuid(string a, string b) => Guid.TryParse(a, out var first)
        && Guid.TryParse(b, out var second) && first == second;

    static HashSet<string> ValidateFixture(JsonObject manifest, JsonObject declared, string manifestPath)
    {
        var version = FixtureVersion(manifest);
        string[] required = ["fixtureVersion", "generatorRules", "corpusSha256", "recordCount", "corpusPath",
            "indexName", "declaredSchemaSha256", "keyword", "queryVector", "vectorDimensions",
            "similarityMetric", "candidateCount", "serviceApi", "pageSize"];
        if (required.Any(key => manifest[key] is null)
            || manifest["recordCount"]!.GetValue<int>() != IndexedRecords(manifest)
            || Text(manifest, "indexName") != IndexName(manifest)
            || Text(manifest, "corpusPath") != "corpus.jsonl"
            || Text(manifest, "keyword") != "maths"
            || Text(manifest, "similarityMetric") != "cosine"
            || manifest["vectorDimensions"]!.GetValue<int>() != 16
            || manifest["candidateCount"]!.GetValue<int>() != 50
            || manifest["pageSize"]!.GetValue<int>() != Top || Text(manifest, "serviceApi") != Api
            || string.IsNullOrWhiteSpace(Text(manifest, "generatorRules")))
            throw new InvalidDataException("Manifest does not describe the approved immutable fixture.");
        if (version == 2)
        {
            const string rules = "SHA256(UTF8(id)); vector=float(byte[0:16]-128); "
                + "content=topic(byte[18]%4), id, maths*(1+byte[16]%7), lesson*(1+byte[17]%23); "
                + "ascending IDs; UTF8 compact JSON separators comma/colon; key order id/content/vector; LF"
                + "; v2: keywordOnly=1..6133; shared=6134..6158 vector=[100,ordinal-6108,0*14]; "
                + "vectorOnly=6159..6183 vector=[100,ordinal-6158,0*14]; "
                + "nonkeyword topic=(ordinal-6159)%4, id, lesson*(1+byte[17]%23)";
            var groups = manifest["membership"]!.AsObject();
            if (Text(manifest, "generatorRules") != rules
                || manifest["keywordMatchCount"]!.GetValue<int>() != Records || groups.Count != 3)
                throw new InvalidDataException("Invalid mixed membership or generator rules.");
            foreach (var (group, start, count) in new[] {
                ("keywordOnly", 1, 6133), ("shared", 6134, 25), ("vectorOnly", 6159, 25) })
                if (!groups[group]!.AsArray().Select(v => v!.GetValue<string>())
                    .SequenceEqual(IdRange(start, count).Order(StringComparer.Ordinal)))
                    throw new InvalidDataException($"Invalid {group} ID range.");
        }
        var queryVector = manifest["queryVector"]!.AsArray();
        if (queryVector.Count != 16 || queryVector.Where((v, i) => v!.GetValue<float>() != (i == 0 ? 1f : 0f)).Any())
            throw new InvalidDataException("Unexpected query vector.");
        if (Hash(Encoding.UTF8.GetBytes(Canonical(declared))) != Text(manifest, "declaredSchemaSha256"))
            throw new InvalidDataException("Declared schema hash mismatch.");
        if (!SchemaEquivalent(ExpectedSchema(IndexName(manifest)), declared)
            || (version == 2 && Canonical(ExpectedSchema(IndexName(manifest))) != Canonical(declared)))
            throw new InvalidDataException("Declared schema differs from the approved index definition.");
        var corpusPath = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(manifestPath)!, Text(manifest, "corpusPath")));
        using (var corpus = File.OpenRead(corpusPath))
            if (Convert.ToHexStringLower(SHA256.HashData(corpus)) != Text(manifest, "corpusSha256"))
                throw new InvalidDataException("Corpus SHA256 mismatch.");
        var corpusBytes = File.ReadAllBytes(corpusPath);
        if (corpusBytes.Length == 0 || corpusBytes[^1] != (byte)'\n' || corpusBytes.Contains((byte)'\r')
            || corpusBytes.AsSpan().StartsWith(new byte[] { 0xef, 0xbb, 0xbf }))
            throw new InvalidDataException("Corpus must be UTF-8 without BOM and use terminal LF line endings.");
        var expected = new HashSet<string>(StringComparer.Ordinal);
        var ordinal = 0;
        var strictUtf8 = new UTF8Encoding(false, true);
        using var stream = File.OpenRead(corpusPath);
        using var reader = new StreamReader(stream, strictUtf8, detectEncodingFromByteOrderMarks: false);
        while (reader.ReadLine() is { } line)
        {
            ordinal++;
            var record = JsonNode.Parse(line)!.AsObject();
            var id = $"doc-{ordinal:D6}";
            var digest = SHA256.HashData(Encoding.UTF8.GetBytes(id));
            var vector = record["vector"]!.AsArray();
            var topic = new[] { "algebra", "geometry", "fractions", "statistics" }[digest[18] % 4];
            var content = string.Join(" ", new[] { topic, id }
                .Concat(Enumerable.Repeat("maths", 1 + digest[16] % 7))
                .Concat(Enumerable.Repeat("lesson", 1 + digest[17] % 23)));
            var expectedVector = digest.Take(16).Select(b => (int)b - 128).ToArray();
            if (version == 2 && ordinal > 6133)
                expectedVector = new[] { 100, ordinal - (ordinal <= Records ? 6108 : Records) }
                    .Concat(Enumerable.Repeat(0, 14)).ToArray();
            if (version == 2 && ordinal > Records)
            {
                topic = new[] { "arithmetic exercises and number practice", "number patterns and calculation practice",
                    "fractions exercises and quantity practice", "geometry exercises and shape practice" }[(ordinal - 6159) % 4];
                content = string.Join(" ", new[] { topic, id }
                    .Concat(Enumerable.Repeat("lesson", 1 + digest[17] % 23)));
            }
            var expectedLine = "{\"id\":\"" + id + "\",\"content\":" + JsonSerializer.Serialize(content, Json)
                + ",\"vector\":[" + string.Join(",", expectedVector.Select(v => v.ToString(CultureInfo.InvariantCulture) + ".0")) + "]}";
            if (!record.Select(property => property.Key).SequenceEqual(new[] { "id", "content", "vector" })
                || record.ToJsonString(Json) != line || Text(record, "id") != id || !expected.Add(id)
                || Text(record, "content") != content || vector.Count != 16
                || vector.Where((v, i) => !float.IsFinite(v!.GetValue<float>())
                    || v.GetValue<float>() != expectedVector[i]).Any()
                || (version == 2 && line != expectedLine)
                || vector.All(v => v!.GetValue<float>() == 0))
                throw new InvalidDataException($"Invalid deterministic corpus record {ordinal}.");
        }
        if (ordinal != IndexedRecords(manifest)) throw new InvalidDataException("Corpus cardinality mismatch.");
        return expected;
    }

    static async Task VerifyPreparedFixture(
        string manifestPath, JsonObject manifest, Dictionary<string, string> environment, SearchClient search)
    {
        var directory = Path.GetDirectoryName(manifestPath)!;
        var receipt = ReadObject(Path.Combine(directory, "preparation.json"));
        var identity = new JsonObject
        {
            ["fixtureVersion"] = 2,
            ["corpusSha256"] = Text(manifest, "corpusSha256"),
            ["declaredSchemaSha256"] = Text(manifest, "declaredSchemaSha256"),
            ["indexName"] = IndexName(manifest),
            ["serviceResourceId"] = environment["AZURE_SEARCH_RESOURCE_ID"],
            ["endpoint"] = environment["AZURE_SEARCH_ENDPOINT"]
        };
        if (!JsonNode.DeepEquals(receipt["identity"], identity) || Text(receipt, "status") != "ready"
            || receipt["uploadedRecordCount"]!.GetValue<int>() != MixedRecords
            || receipt["checkedSuccessCount"]!.GetValue<int>() != MixedRecords
            || Text(receipt, "schemaEvidenceFile") != "actual-schema.json")
            throw new InvalidDataException("A matching ready mixed-fixture receipt is required.");
        var uploads = receipt["uploadResults"]!.AsArray();
        if (uploads.Count != MixedRecords || uploads.Any(row => row!["succeeded"]!.GetValue<bool>() != true)
            || !uploads.Select(row => row!["key"]!.GetValue<string>()).SequenceEqual(IdRange(1, MixedRecords).Order(StringComparer.Ordinal)))
            throw new InvalidDataException("All 6,183 successful individual upload results are required.");
        var schemaBytes = File.ReadAllBytes(Path.Combine(directory, "actual-schema.json"));
        if (Hash(schemaBytes) != Text(receipt, "schemaEvidenceSha256")
            || !SchemaEquivalent(ExpectedSchema(IndexName(manifest)), JsonNode.Parse(schemaBytes)!))
            throw new InvalidDataException("Preparation schema evidence differs.");
        if ((await search.GetDocumentCountAsync()).Value != MixedRecords)
            throw new InvalidDataException("Prepared mixed indexed count differs.");
        var expected = File.ReadLines(Path.Combine(directory, "corpus.jsonl"))
            .Select(line => JsonNode.Parse(line)!.AsObject()).ToArray();
        var options = new SearchOptions();
        options.Select.Add("id");
        options.Select.Add("content");
        options.OrderBy.Add("id asc");
        var response = await search.SearchAsync<SearchDocument>("*", options);
        var ordinal = 0;
        await foreach (var row in response.Value.GetResultsAsync())
        {
            if (ordinal >= expected.Length
                || row.Document["id"].ToString() != Text(expected[ordinal], "id")
                || row.Document["content"].ToString() != Text(expected[ordinal], "content"))
                throw new InvalidDataException("Mixed ID/content inventory differs from the verified fixture.");
            ordinal++;
        }
        if (ordinal != MixedRecords) throw new InvalidDataException("Mixed inventory is incomplete.");
    }

    static JsonObject ExpectedSchema(string name = "hybrid-pagination-debug")
    {
        var schema = JsonNode.Parse("""
        {"name":"hybrid-pagination-debug","fields":[
        {"name":"id","type":"Edm.String","key":true,"searchable":false,"retrievable":true},
        {"name":"content","type":"Edm.String","searchable":true,"analyzer":"standard.lucene","retrievable":true},
        {"name":"vector","type":"Collection(Edm.Single)","searchable":true,"dimensions":16,"vectorSearchProfile":"exact-profile"}],
        "vectorSearch":{"algorithms":[{"name":"exact","exhaustiveKnnParameters":{"metric":"cosine"},"kind":"exhaustiveKnn"}],
        "profiles":[{"name":"exact-profile","algorithm":"exact"}]}}
        """)!.AsObject();
        schema["name"] = name;
        return schema;
    }

    // Compare effective settings, not service-added defaults or SDK-specific omitted nulls.
    static bool SchemaEquivalent(JsonNode declared, JsonNode actual) =>
        JsonNode.DeepEquals(NormalizeSchema(declared, ""), NormalizeSchema(actual, ""));

    static JsonNode? NormalizeSchema(JsonNode? node, string parent)
    {
        if (node is JsonObject obj)
        {
            var result = new JsonObject();
            foreach (var entry in obj.OrderBy(e => e.Key, StringComparer.Ordinal))
            {
                var key = entry.Key;
                var value = entry.Value;
                if (key is "@odata.etag" or "@odata.context" || value is null || value is JsonArray { Count: 0 }) continue;
                if (value is JsonValue scalar)
                {
                    if (parent == "fields" && scalar.TryGetValue<bool>(out var boolean))
                    {
                        var scalarString = obj["type"]?.GetValue<string>() == "Edm.String";
                        bool? defaultValue = key switch
                        {
                            "key" or "searchable" => false,
                            "stored" => true,
                            "retrievable" or "filterable" or "sortable" or "facetable" => scalarString,
                            _ => null
                        };
                        if (boolean == defaultValue) continue;
                    }
                    if ((key == "normalizer" || key == "searchAnalyzer" || key == "indexAnalyzer")
                        && scalar.ToJsonString() == "\"\"") continue;
                    if (parent == "similarity" && key == "@odata.type"
                        && scalar.ToJsonString() == "\"#Microsoft.Azure.Search.BM25Similarity\"") continue;
                    if (parent == "similarity" && key == "k1" && scalar.GetValue<double>() == 1.2) continue;
                    if (parent == "similarity" && key == "b" && scalar.GetValue<double>() == 0.75) continue;
                }
                var normalized = NormalizeSchema(value, key);
                if (normalized is JsonObject { Count: 0 }) continue;
                result[key] = normalized;
            }
            return result;
        }
        if (node is JsonArray array)
        {
            var normalized = array.Select(item => NormalizeSchema(item, parent)).ToList();
            if (normalized.All(item => item is JsonObject o && o["name"] is not null))
                normalized = normalized.OrderBy(item => item!["name"]!.GetValue<string>(), StringComparer.Ordinal).ToList();
            return new JsonArray(normalized.ToArray());
        }
        return node?.DeepClone();
    }

    internal static JsonObject QueryBody(string queryCase, JsonObject manifest)
    {
        var body = new JsonObject
        {
            ["count"] = true, ["select"] = new JsonArray("id"), ["top"] = Top,
            ["queryType"] = "simple", ["searchMode"] = "any", ["vectorFilterMode"] = "preFilter"
        };
        if (queryCase != "vector")
        {
            body["search"] = "maths";
            body["searchFields"] = new JsonArray("content");
        }
        if (queryCase != "keyword")
            body["vectorQueries"] = new JsonArray(new JsonObject
            {
                ["kind"] = "vector", ["vector"] = manifest["queryVector"]!.DeepClone(),
                ["fields"] = "vector", ["k"] = 50, ["exhaustive"] = true
            });
        return body;
    }

    internal static JsonObject NormalizeRequest(JsonObject body)
    {
        var result = body.DeepClone().AsObject();
        foreach (var name in new[] { "select", "searchFields" })
            if (result[name] is JsonValue value && value.TryGetValue<string>(out var fields))
                result[name] = new JsonArray(fields.Split(',').Select(f => (JsonNode?)JsonValue.Create(f.Trim())).ToArray());
        result["queryType"] ??= JsonValue.Create("simple");
        result["searchMode"] ??= JsonValue.Create("any");
        result["vectorFilterMode"] ??= JsonValue.Create("preFilter");
        return result;
    }

    static JsonObject? WithoutSkip(JsonObject? body)
    {
        var result = body?.DeepClone().AsObject();
        result?.Remove("skip");
        return result;
    }

    static IEnumerable<PageObservation> Primary(CaseReport report, List<PageObservation> observations) =>
        observations.Where(o => o.Phase == "scan" && o.Error is null && o.IncompleteReason is null
            && o.RowCount is not null && (report.Summary.ScanBasis == "vector-k"
                ? o.Skip < report.Summary.ScanPageCount * Top
                : o.Advertised));

    static void Summarize(CaseReport report, List<PageObservation> observations, HashSet<string> expected)
    {
        if (report.Case == "keyword") expected = IdRange(1, Records);
        var summary = report.Summary;
        var primary = Primary(report, observations).ToArray();
        var allIds = primary.SelectMany(o => o.Ids!).ToArray();
        summary.ReachableIds = allIds.Distinct().Order(StringComparer.Ordinal).ToArray();
        summary.UniqueReachableIds = summary.ReachableIds.Length;
        summary.TotalRows = allIds.Length;
        summary.DuplicateIds = allIds.GroupBy(id => id).Where(g => g.Count() > 1)
            .OrderBy(g => g.Key, StringComparer.Ordinal).ToDictionary(g => g.Key, g => g.Count());
        summary.MissingExpectedKeywordIds = report.Case == "keyword"
            ? expected.Except(summary.ReachableIds).Order(StringComparer.Ordinal).ToArray() : null;
        summary.ObservedCounts = observations.Where(o => o.ReportedCount is not null)
            .Select(o => o.ReportedCount!.Value).Distinct().Order().ToArray();
        summary.CountChanged = summary.ObservedCounts.Length > 1;
        summary.PopulatedPages = primary.Count(o => o.RowCount > 0);
        summary.EmptyPages = primary.Count(o => o.RowCount == 0);
        summary.FirstEmptyPage = primary.FirstOrDefault(o => o.RowCount == 0)?.PageNumber;
        summary.LastPopulatedPage = primary.LastOrDefault(o => o.RowCount > 0)?.PageNumber;
        summary.ScanCoverage = summary.ScanPageCount is int required
            ? required == 0
                ? observations.Any(o => o.Phase == "scan" && o.Error is null && o.IncompleteReason is null) ? 1d : 0d
                : (double)primary.Length / required : null;
        summary.AdvertisedPageCoverage = summary.ScanBasis == "advertised-count" ? summary.ScanCoverage : null;
        summary.ReportedMinusReachable = summary.ScanBasis == "advertised-count"
            ? summary.ReportedCount - summary.UniqueReachableIds : null;
        summary.BaselineValid = report.Case == "keyword"
            ? summary.ReportedCount == Records && summary.UniqueReachableIds == Records
                && summary.TotalRows == Records && summary.DuplicateIds.Count == 0
                && summary.MissingExpectedKeywordIds!.Length == 0 && summary.AdvertisedPages == 1232
                && summary.PopulatedPages == 1232 && primary.LastOrDefault()?.RowCount == 3
                && !summary.CountChanged && summary.IndexCountStart == IndexedRecords(report.Fixture)
                && summary.IndexCountEnd == IndexedRecords(report.Fixture)
            : null;
        summary.VectorMembershipValid = FixtureVersion(report.Fixture) == 2 && report.Case == "vector"
            ? summary.ReachableIds.ToHashSet(StringComparer.Ordinal).SetEquals(IdRange(6134, 50))
                && summary.DuplicateIds.Count == 0 : null;
    }

    static JsonObject Failure(RequestFailedException error) => new()
    {
        ["type"] = error.GetType().Name, ["status"] = error.Status,
        ["errorCode"] = error.ErrorCode, ["message"] = error.Message
    };
    static string PackageVersion(Assembly assembly) =>
        assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()!.InformationalVersion.Split('+')[0];
    static JsonObject ReadObject(string path) => JsonNode.Parse(File.ReadAllText(path))!.AsObject();
    static string Text(JsonObject obj, string name) => obj[name]!.GetValue<string>();
    static string Hash(byte[] bytes) => Convert.ToHexStringLower(SHA256.HashData(bytes));
    static string Canonical(JsonNode node) => Sort(node)!.ToJsonString(Json);
    static JsonNode? Sort(JsonNode? node) => node switch
    {
        JsonObject obj => new JsonObject(obj.OrderBy(kv => kv.Key, StringComparer.Ordinal)
            .Select(kv => KeyValuePair.Create(kv.Key, Sort(kv.Value)))),
        JsonArray array => new JsonArray(array.Select(Sort).ToArray()),
        _ => node?.DeepClone()
    };
    static void WriteReport(string path, CaseReport report)
    {
        var pending = path + ".pending";
        using (var file = new FileStream(pending, FileMode.Create, FileAccess.Write))
        {
            JsonSerializer.Serialize(file, report, Json);
            file.Flush(true);
        }
        File.Move(pending, path, overwrite: true);
    }
}

sealed class CapturePolicy : HttpPipelinePolicy
{
    public int SendCount { get; private set; }
    public string? ApiVersion { get; private set; }
    public string? Method { get; private set; }
    public string? Path { get; private set; }
    public JsonObject? NormalizedRequest { get; private set; }
    public int? StatusCode { get; private set; }
    public string? RequestId { get; private set; }
    public void Reset()
    {
        SendCount = 0;
        ApiVersion = Method = Path = RequestId = null;
        NormalizedRequest = null;
        StatusCode = null;
    }
    void Capture(HttpMessage message, MemoryStream content)
    {
        SendCount++;
        var uri = message.Request.Uri.ToUri();
        Path = uri.AbsolutePath;
        Method = message.Request.Method.Method;
        ApiVersion = uri.Query.TrimStart('?').Split('&')
            .Select(part => part.Split('=', 2)).Where(parts => parts[0] == "api-version")
            .Select(parts => Uri.UnescapeDataString(parts[1])).SingleOrDefault();
        if (content.Length > 0)
            NormalizedRequest = Experiment.NormalizeRequest(JsonNode.Parse(content.ToArray())!.AsObject());
    }
    void CaptureResponse(HttpMessage message)
    {
        if (!message.HasResponse) return;
        StatusCode = message.Response.Status;
        RequestId = message.Response.Headers.TryGetValue("request-id", out var id) ? id
            : message.Response.Headers.TryGetValue("x-ms-request-id", out id) ? id : null;
    }
    public override void Process(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        using var content = new MemoryStream();
        message.Request.Content?.WriteTo(content, message.CancellationToken);
        Capture(message, content);
        try { ProcessNext(message, pipeline); }
        finally { CaptureResponse(message); }
    }
    public override async ValueTask ProcessAsync(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        using var content = new MemoryStream();
        if (message.Request.Content is not null)
            await message.Request.Content.WriteToAsync(content, message.CancellationToken);
        Capture(message, content);
        try { await ProcessNextAsync(message, pipeline); }
        finally { CaptureResponse(message); }
    }
}

sealed class CaseReport
{
    public int SchemaVersion { get; init; } = 1;
    public required string RunId { get; init; }
    public string Language { get; init; } = "dotnet";
    public required string Case { get; init; }
    public required JsonObject Fixture { get; init; }
    public required JsonObject Index { get; init; }
    public required Dictionary<string, string> Environment { get; init; }
    public required JsonObject Client { get; init; }
    public required JsonObject Query { get; init; }
    public DateTimeOffset StartedAt { get; init; } = DateTimeOffset.UtcNow;
    public DateTimeOffset? FinishedAt { get; set; }
    public string Status { get; set; } = "incomplete";
    public string Outcome { get; set; } = "blocked/incomplete";
    public List<string> Reasons { get; } = [];
    public required string ObservationsFile { get; init; }
    public CaseSummary Summary { get; } = new();
    public List<Boundary> Boundaries { get; } = [];
    public List<JsonObject> Errors { get; } = [];
    public string[] Limitations { get; } =
    [
        "No writes are permitted during measurement; start/end counts alone cannot prove immutability.",
        "Offset requests are independent, not a snapshot. Equal-score ordering is not guaranteed.",
        "Documented hybrid recall defaults are a hypothesis, not a measured candidate-window guarantee.",
        "This synthetic pinned-SDK baseline does not establish customer parity, a customer SDK defect, production suitability, or GA timing."
    ];
}

sealed class PageObservation
{
    public required string RunId { get; init; }
    public string Language { get; init; } = "dotnet";
    public required string Case { get; init; }
    public required string Phase { get; init; }
    public int PageNumber { get; init; }
    public int Skip { get; init; }
    public int Top { get; init; } = Experiment.Top;
    public bool Advertised { get; set; }
    public string[]? Ids { get; set; }
    public double?[]? Scores { get; set; }
    public int? RowCount { get; set; }
    public long? ReportedCount { get; set; }
    public DateTimeOffset Timestamp { get; init; } = DateTimeOffset.UtcNow;
    public string? ApiVersion { get; set; }
    public string? Method { get; set; }
    public string? Path { get; set; }
    public JsonObject? NormalizedRequest { get; set; }
    public int SendCount { get; set; }
    public int? StatusCode { get; set; }
    public string? RequestId { get; set; }
    public bool Continuation { get; set; }
    public string? IncompleteReason { get; set; }
    public JsonObject? Error { get; set; }
    public void CopyCapture(CapturePolicy capture)
    {
        ApiVersion = capture.ApiVersion;
        Method = capture.Method;
        Path = capture.Path;
        NormalizedRequest = capture.NormalizedRequest?.DeepClone().AsObject();
        SendCount = capture.SendCount;
        StatusCode = capture.StatusCode;
        RequestId = capture.RequestId;
    }
}

sealed class CaseSummary
{
    public string? ScanBasis { get; set; }
    public int? ScanPageCount { get; set; }
    public long? ReportedCount { get; set; }
    public int? AdvertisedPages { get; set; }
    public double? AdvertisedPageCoverage { get; set; }
    public long? ReportedMinusReachable { get; set; }
    public double? ScanCoverage { get; set; }
    public long[] ObservedCounts { get; set; } = [];
    public bool CountChanged { get; set; }
    public int TotalRows { get; set; }
    public int UniqueReachableIds { get; set; }
    public string[] ReachableIds { get; set; } = [];
    public Dictionary<string, int> DuplicateIds { get; set; } = [];
    public string[]? MissingExpectedKeywordIds { get; set; }
    public int PopulatedPages { get; set; }
    public int EmptyPages { get; set; }
    public int? FirstEmptyPage { get; set; }
    public int? LastPopulatedPage { get; set; }
    public long? IndexCountStart { get; set; }
    public long? IndexCountEnd { get; set; }
    public bool? BaselineValid { get; set; }
    public bool? VectorMembershipValid { get; set; }
}

sealed class Boundary
{
    public int Skip { get; init; }
    public required int[] ObservationIndexes { get; init; }
    public bool? CountAgreement { get; init; }
    public bool SizeAgreement { get; init; }
    public bool IdSetAgreement { get; init; }
    public bool OrderAgreement { get; init; }
}
