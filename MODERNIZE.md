# Modernization Plan: .NET Framework 4.8 → .NET 10 (Windows + Linux)

Goal: convert the legacy-format VB.NET WinForms project to SDK-style projects targeting
`net10.0-windows`, so `dotnet build` succeeds on both Windows and Linux.

## Current state

- **Main app** (`Kuid2Hash.vbproj`): legacy-format VB.NET WinForms, .NET Framework 4.8,
  `WinExe`, My Application model (auto-generated `MyApplication` startup object), no NuGet
  packages — only framework references.
- **Tests** (`Kuid2Hash.Tests\Kuid2Hash.Tests.csproj`): legacy-format C# MSTest project
  referencing the main project; tests call `frmKuid`'s shared methods directly.
- The actual logic is small and pure: 4 shared functions in `frmKuid.vb`
  (`HexToKuid`, `KuidToHex`, `ComputeHash`, `ConvertHex`) plus an instance method `RevKuid`.
  UI code (event handlers) lives in the same file.

## Key decisions / gotchas

1. **WinForms on Linux**: .NET 10 supports WinForms cross-platform — it *compiles* fine on
   Linux, but can't run without a display. So "compile successfully on both" is achievable;
   running on Linux needs X/Wayland (or just don't run the UI there).
2. **`Process.Start("https://...")`** (`frmKuid.vb`, `LinkLabel1_LinkClicked`) throws on
   .NET Core+ without an overload — must become:
   ```vb
   Process.Start(New ProcessStartInfo(url) With { .UseShellExecute = True })
   ```
3. **My Application model**: Abandoned. SDK-style VB projects with `<StartupObject>Sub Main</StartupObject>`
   and a plain `Module Program` with `Sub Main()` work correctly. The My Application model
   (`My Project\Application.myapp`, `Application.Designer.vb`) is not needed and was removed.
   **Key gotcha**: `StartupObject` must be set to `Sub Main` (not `Program` or `Kuid2Hash.Program`).
4. **Tests reference UI types**: they call `frmKuid.KuidToHex(...)` etc. Keeping
   `<UseWindowsForms>true</UseWindowsForms>` in the test project makes this compile on both
   platforms (WinForms compiles cross-platform; only *running* needs a display). Decoupling
   the logic is optional (Phase 4).
5. **`App.config`**: contains only the runtime version tag — delete it (or leave as inert
   `<None>`).

## Phases

### Phase 1 — Convert main project to SDK-style (.NET 10 WinForms)

Replace `Kuid2Hash.vbproj` with:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <RootNamespace>Kuid2Hash</RootNamespace>
    <AssemblyName>Kuid2Hash</AssemblyName>
    <TargetFramework>net10.0-windows</TargetFramework>
    <UseWindowsForms>true</UseWindowsForms>
    <ApplicationIcon>Chromatix-Keyboard-Keys-Hash.ico</ApplicationIcon>
    <StartupObject>Sub Main</StartupObject>
  </PropertyGroup>
</Project>
```

Notes:
- SDK-style auto-includes all `.vb` and `.resx` files, so the explicit `Compile`,
  `EmbeddedResource`, `Reference`, and `Import` item groups disappear.
- Delete `My Project\*` files (or exclude via `<Compile Remove="My Project\**" />`).
- Delete `App.config`.
- **Critical**: `<StartupObject>` must be `Sub Main`, not `Program` or a fully-qualified name.

Code fix in `frmKuid.vb`:

```vb
Private Sub LinkLabel1_LinkClicked(sender As Object, e As LinkLabelLinkClickedEventArgs) Handles LinkLabel1.LinkClicked
    Process.Start(New ProcessStartInfo("https://github.com/SilverGreen93/Kuid2Hash") With { .UseShellExecute = True })
End Sub
```

### Phase 2 — Convert test project to SDK-style (.NET 10)

Replace `Kuid2Hash.Tests\Kuid2Hash.Tests.csproj` with:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0-windows</TargetFramework>
    <UseWindowsForms>true</UseWindowsForms>   ' tests touch frmKuid (a WinForms type)
    <IsPackable>false</IsPackable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="MSTest.TestAdapter" Version="3.8.x" />
    <PackageReference Include="MSTest.TestFramework" Version="3.8.x" />
  </ItemGroup>
</Project>
```

Notes:
- Update MSTest from 2.2.10 → latest 3.x (2.x is EOL).
- The `ProjectReference` to the main project becomes implicit via SDK-style globbing? No —
  keep it explicit:
  ```xml
  <ItemGroup>
    <ProjectReference Include="..\Kuid2Hash.vbproj" />
  </ItemGroup>
  ```

### Phase 3 — Solution + cross-platform verification

- The `.sln` stays as-is (project GUIDs unchanged, same file names/paths).
- Verify on Windows: `dotnet build Kuid2Hash.sln -c Release && dotnet test`.
- Verify on Linux (WSL/container or CI): same commands — WinForms compiles fine; only
  *running* the UI needs a display.

### Phase 4 (optional, recommended) — Decouple logic from UI

Move the pure functions (`HexToKuid`, `KuidToHex`, `ComputeHash`, `ConvertHex`, `RevKuid`)
into a new static class `KuidConverter.vb`; have `frmKuid` delegate to it. Benefits:
- Tests reference no WinForms types at all (test project can drop `<UseWindowsForms>`).
- Enables a future console/CLI target sharing the same logic.

### Phase 5 (optional) — CI

Add a GitHub Actions workflow with two jobs (`windows-latest` and `ubuntu-latest`), each
running:

```yaml
- run: dotnet build Kuid2Hash.sln -c Release
- run: dotnet test --no-build
```

## Verification checklist

- [ ] `dotnet build Kuid2Hash.sln -c Release` succeeds on Windows
- [ ] `dotnet test` passes (all existing MSTest cases)
- [ ] `dotnet build Kuid2Hash.sln -c Release` succeeds on Linux
- [ ] App still runs correctly on Windows (kuid ↔ hex conversion, hash display, reverse checkbox, link label)
