using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Kuid2Hash.Tests
{
    /// <summary>
    /// Validates the kuid conversions of frmKuid against a small CSV data set.
    /// For every row both conversion directions are checked (string -> bytes and
    /// bytes -> string) as well as the hash, which must be identical no matter
    /// which direction produced the byte array.
    /// </summary>
    [TestClass]
    public class KuidConversionTests
    {
        // StrKuid,BinKuid,Hash
        private const string CsvData =
            "kuid 68787 1097,B3 0C 01 00 49 04 00 00,F3\r\n" +
            "kuid2 328583 1373 2,87 03 05 04 5D 05 00 00,D9\r\n" +
            "kuid2 146087 21661 127,A7 3A 02 FE 9D 54 00 00,56\r\n" +
            "kuid -2 1009,FE FF FF FF F1 03 00 00,F3\r\n" +
            "kuid 251996 -420662835,5C D8 03 00 CD 31 ED E6,70\r\n" +
            "kuid2 46819 15218 1,E3 B6 00 02 72 3B 00 00,1C\r\n" +
            "kuid -1 569,39 02 00 00,3B\r\n" +
            "kuid -1 100468,74 88 01 00,FD";

        private sealed class KuidRow
        {
            public string StrKuid;
            public byte[] BinKuid;
            public byte Hash;
        }

        /// <summary>Parses the CSV data set into test rows.</summary>
        private static IEnumerable<KuidRow> ParseCsv(string csv)
        {
            foreach (var line in csv.Split(new[] { "\r\n", "\n" }, StringSplitOptions.RemoveEmptyEntries))
            {
                var parts = line.Split(',');
                Assert.AreEqual(3, parts.Length, "CSV row must have exactly 3 columns: " + line);

                yield return new KuidRow
                {
                    StrKuid = parts[0].Trim(),
                    BinKuid = ParseHex(parts[1]),
                    Hash = byte.Parse(parts[2].Trim(), NumberStyles.HexNumber)
                };
            }
        }

        private static byte[] ParseHex(string hex)
        {
            var bytes = new List<byte>();
            foreach (var token in hex.Split(new[] { ' ', '-', ':', ',' }, StringSplitOptions.RemoveEmptyEntries))
            {
                bytes.Add(byte.Parse(token, NumberStyles.HexNumber));
            }
            return bytes.ToArray();
        }

        private static string ToHex(byte[] bytes) => BitConverter.ToString(bytes).Replace("-", " ");

        /// <summary>
        /// String -> bytes: every kuid string must convert to exactly the binary form from the CSV.
        /// (For uid -1 kuids only the 4 content id bytes are expected, the FF FF FF FF user part is implicit.)
        /// </summary>
        [TestMethod]
        public void KuidToHex_MatchesExpectedBinary()
        {
            var cases = new (string StrKuid, string ExpectedBin)[]
            {
                ("kuid 68787 1097", "B3 0C 01 00 49 04 00 00"),
                ("kuid2 328583 1373 2", "87 03 05 04 5D 05 00 00"),
                ("kuid2 146087 21661 127", "A7 3A 02 FE 9D 54 00 00"),
                ("kuid -2 1009", "FE FF FF FF F1 03 00 00"),
                ("kuid 251996 -420662835", "5C D8 03 00 CD 31 ED E6"),
                ("kuid2 46819 15218 1", "E3 B6 00 02 72 3B 00 00"),
                ("kuid -1 569", "39 02 00 00"),
                ("kuid -1 100468", "74 88 01 00"),
            };
            foreach (var (strKuid, expectedBin) in cases)
            {
                var actual = frmKuid.KuidToHex(strKuid);
                CollectionAssert.AreEqual(expectedBin.Split(' '), ToHex(actual).Split(' '),
                    $"KuidToHex(\"{strKuid}\") should be \"{expectedBin}\"");
            }
        }

        /// <summary>
        /// Bytes -> string: every binary kuid from the CSV must convert back to a valid kuid string.
        /// The round-tripped string must parse again to exactly the same bytes (both directions work).
        /// </summary>
        [TestMethod]
        public void HexToKuid_RoundTripsBackToSameBytes()
        {
            var bins = new[]
            {
                "B3 0C 01 00 49 04 00 00",
                "87 03 05 04 5D 05 00 00",
                "A7 3A 02 FE 9D 54 00 00",
                "FE FF FF FF F1 03 00 00",
                "5C D8 03 00 CD 31 ED E6",
                "E3 B6 00 02 72 3B 00 00",
                "39 02 00 00",
                "74 88 01 00",
            };
            foreach (var bin in bins)
            {
                var bytes = ParseHex(bin);

                // direction: binary -> string (a uid -1 kuid is printed as "<kuid:-1:...>")
                var strKuid = frmKuid.HexToKuid(bytes);
                Assert.IsTrue(strKuid.StartsWith("<kuid") && strKuid.EndsWith(">"),
                    $"HexToKuid(\"{bin}\") should return a bracketed kuid, got \"{strKuid}\"");

                // direction: string -> binary again must give exactly the same bytes back
                var roundTripped = frmKuid.KuidToHex(strKuid);
                CollectionAssert.AreEqual(bytes, roundTripped,
                    $"Round trip of \"{bin}\" via \"{strKuid}\" should return the original bytes");
            }
        }

        /// <summary>
        /// Hash: for every row the hash must match the CSV value, computed from both the
        /// string-derived and the binary-derived byte arrays (they are identical).
        /// </summary>
        [TestMethod]
        public void ComputeHash_MatchesExpectedValue()
        {
            var cases = new (string StrKuid, string Bin, string ExpectedHash)[]
            {
                ("kuid 68787 1097", "B3 0C 01 00 49 04 00 00", "F3"),
                ("kuid2 328583 1373 2", "87 03 05 04 5D 05 00 00", "D9"),
                ("kuid2 146087 21661 127", "A7 3A 02 FE 9D 54 00 00", "56"),
                ("kuid -2 1009", "FE FF FF FF F1 03 00 00", "F3"),
                ("kuid 251996 -420662835", "5C D8 03 00 CD 31 ED E6", "70"),
                ("kuid2 46819 15218 1", "E3 B6 00 02 72 3B 00 00", "1C"),
                ("kuid -1 569", "39 02 00 00", "3B"),
                ("kuid -1 100468", "74 88 01 00", "FD"),
            };
            foreach (var (strKuid, bin, expectedHash) in cases)
            {
                var fromString = frmKuid.KuidToHex(strKuid);
                var fromBinary = ParseHex(bin);

                // both directions must produce the same byte array ...
                CollectionAssert.AreEqual(fromBinary, fromString,
                    $"\"{strKuid}\" and \"{bin}\" should be the same kuid");

                // ... so the hash is identical either way and matches the CSV value
                var expected = byte.Parse(expectedHash, NumberStyles.HexNumber);
                Assert.AreEqual(expected, frmKuid.ComputeHash(fromString),
                    $"computeHash(\"{strKuid}\") should be 0x{expected:X2}");
                Assert.AreEqual(expected, frmKuid.ComputeHash(fromBinary),
                    $"computeHash(\"{bin}\") should be 0x{expected:X2}");
            }
        }

        /// <summary>
        /// Full CSV validation: parses the data set and checks every row in one go -
        /// string -> binary, binary -> string round trip, and hash from both directions.
        /// </summary>
        [TestMethod]
        public void CsvDataSet_AllRowsConvertBothWaysAndHashIsCorrect()
        {
            var rows = ParseCsv(CsvData).ToList();
            Assert.AreEqual(8, rows.Count, "The CSV data set should contain 8 rows");

            foreach (var row in rows)
            {
                // direction 1: string -> binary must equal the CSV column
                var fromString = frmKuid.KuidToHex(row.StrKuid);
                CollectionAssert.AreEqual(row.BinKuid, fromString,
                    $"Row \"{row.StrKuid}\": KuidToHex should return {ToHex(row.BinKuid)}");

                // direction 2: binary -> string must round-trip back to the same bytes
                var str = frmKuid.HexToKuid(row.BinKuid);
                CollectionAssert.AreEqual(row.BinKuid, frmKuid.KuidToHex(str),
                    $"Row \"{row.StrKuid}\": HexToKuid returned \"{str}\" which does not parse back to {ToHex(row.BinKuid)}");

                // hash must be correct from both directions
                Assert.AreEqual(row.Hash, frmKuid.ComputeHash(fromString),
                    $"Row \"{row.StrKuid}\": hash of string-derived bytes should be 0x{row.Hash:X2}");
                Assert.AreEqual(row.Hash, frmKuid.ComputeHash(row.BinKuid),
                    $"Row \"{row.StrKuid}\": hash of binary-derived bytes should be 0x{row.Hash:X2}");
            }
        }

        /// <summary>
        /// A uid -1 kuid must always be printed with its user part ("<kuid:-1:...>") and
        /// the Reverse kuid checkbox has no effect on it (revKuid is never applied to 4 byte kuids).
        /// </summary>
        [TestMethod]
        public void UidMinusOne_IsPrintedWithUserPart()
        {
            var str = frmKuid.HexToKuid(ParseHex("39 02 00 00"));
            Assert.AreEqual("<kuid:-1:569>", str);

            // the full 8 byte form must print identically (FF FF FF FF user part)
            var strFull = frmKuid.HexToKuid(ParseHex("FF FF FF FF 39 02 00 00"));
            Assert.AreEqual(str, strFull);
        }
    }
}
