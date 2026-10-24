"""Generate the full reverse-engineering campaign work queue.

Every BC-own function with unit attribution becomes a work item, grouped by
unit and ordered so foundational modules are covered first. The output is one
address file per batch, ready for `ghidra-persistent.py batch`, plus a progress
ledger so the campaign can resume across sessions.

Batch sizing: ~400 functions per Ghidra invocation keeps each run under a few
minutes while amortizing the project-open cost.
"""
import json
import pathlib
import collections

ROOT = pathlib.Path(r"D:\Rea\extracted")
QUEUE = ROOT / "campaign"
QUEUE.mkdir(exist_ok=True)

attr = json.loads((ROOT / "function-attribution.json").read_text(encoding="utf-8"))
mods = json.loads((ROOT / "source-modules.json").read_text(encoding="utf-8"))
third_party = {p.split("\\")[-1] for p in mods["path_to_functions"] if "ThirdParty" in p}

unit_to_path: dict[str, str] = {}
for path in mods["path_to_functions"]:
    unit_to_path[path.split("\\")[-1]] = path

# Campaign order: foundational layers first, then engines, then UI last.
PHASES = [
    ("01-foundation", ["SsClasses.pas", "SsPersistent.pas", "SsXML.pas", "SsLineList.pas",
                       "SsLineParse.pas", "SsStrProcs.pas", "SsCodePage.pas", "SsMapTree.pas",
                       "SsFileAPI.pas", "SsRegistry.pas", "SsEditStack.pas", "SsBcd.pas",
                       "SsGraphics.pas", "SsSingleInst.pas"]),
    ("02-text-engine", ["TextContent.pas", "TextMap.pas", "TextSession.pas", "TextFormat.pas",
                        "TextFiltered.pas", "TextOutput.pas", "TextREParser.pas",
                        "DlgTextGoTo.pas", "DlgTextFindInFiles.pas", "DlgTextGrammarItem.pas",
                        "DlgTextInsigItem.pas", "DlgTextReplacementItem.pas", "DlgTextReport.pas"]),
    ("03-bc-core", ["BcAlign.pas", "BcAlignLines.pas", "BcFileFormat.pas", "BcSyntaxElements.pas",
                    "BcSession.pas", "BcLineSession.pas", "BcJobs.pas", "BcFileSessionJobs.pas",
                    "BcActions.pas", "BcViews.pas", "BcGeneralPrefs.pas", "BcPrefs.pas",
                    "BcProfile.pas", "BcColors.pas", "BcVersion.pas"]),
    ("04-folder", ["DirSession.pas", "DirSessionState.pas", "DirTree.pas", "DirTreeView.pas",
                   "DirFilters.pas", "DirColors.pas", "ViewDir.pas", "ViewDirBase.pas",
                   "ViewDirSync.pas", "OpBase.pas", "OpCopy.pas", "OpMoveBoth.pas", "OpSync.pas",
                   "DlgDirAlignWithItem.pas", "DlgDirFind.pas", "DlgDirLegend.pas",
                   "DlgDirOpErrors.pas", "DlgDirOtherFilterItem.pas", "DlgDirReport.pas",
                   "DlgDirScript.pas", "FrameDirOpProgress.pas", "FrameDirSessionComparison.pas"]),
    ("05-merge", ["FrameLineAlignDef.pas", "DlgTagReport.pas", "FrameTagSession.pas",
                  "BcTagSession.pas", "BcAsyncSync.pas"]),
    ("06-table-hex-reg", ["TableContent.pas", "TableDetect.pas", "TableFiltered.pas",
                          "TableMap.pas", "TableRules.pas", "TableSession.pas", "ViewTable.pas",
                          "HexContent.pas", "HexFiltered.pas", "HexMap.pas", "HexSession.pas",
                          "ViewHex.pas", "RegContent.pas", "RegMap.pas", "RegSession.pas",
                          "ViewReg.pas", "VerContent.pas", "VerRules.pas", "ViewVer.pas"]),
    ("07-pix-media-ver", ["PixColors.pas", "PixContent.pas", "PixMap.pas", "PixRules.pas",
                          "ViewPix.pas", "MediaContent.pas", "ViewMedia.pas"]),
    ("08-reports", ["BcReport.pas", "DlgReport.pas", "DlgQuickCompare.pas", "BcSpecDlgs.pas",
                    "DlgFileFormatManager.pas", "FrameFileFormat.pas",
                    "FrameFileFormatConversion.pas", "FrameFileSessionFormats.pas",
                    "DlgExport.pas", "DlgImport.pas", "DlgProfileManager.pas",
                    "DlgWorkspaceManager.pas", "DlgProgOptions.pas", "DlgFileConfirmSave.pas",
                    "DlgProfileBrowse.pas", "DlgProfileFileOpen.pas", "DlgProfileSaveAs.pas",
                    "DlgSessionSaveAs.pas", "DlgBrowseRegistry.pas", "FrameSession.pas",
                    "FrameProfile.pas", "FrameProfileBrowseRemote.pas", "BcDropFiles.pas",
                    "BcDynImages.pas", "BcImages.pas", "BcExplorerMenu.pas", "BcForms.pas",
                    "BcLog.pas", "BcStartup.pas", "BcTranslateDFMs.pas", "BcUpgrade3.pas",
                    "BcUpgrade4.pas", "ViewFile.pas", "ViewGeneral.pas", "ViewHome.pas",
                    "ViewSession.pas", "BcExternalSession.pas", "BcClearCase.pas",
                    "BcSccPrefs.pas"]),
    ("09-vfs", ["VfsEntryImpl.pas", "VfsMain.pas", "VfsManagerImpl.pas", "VfsFileCache.pas",
                "VfsJobs.pas", "VfsLocalResourceImpl.pas", "VfsArchiveResourceImpl.pas",
                "Vfs7zipResourceImpl.pas", "VfsAbArchiveResourceImpl.pas",
                "VfsFtpResourceImpl.pas", "VfsFtpIndy10Connection.pas",
                "VfsWebDAVResourceImpl.pas", "VfsAmazonS3ResourceImpl.pas",
                "VfsOneDriveResourceImpl.pas", "VfsPortableDeviceResourceImpl.pas",
                "VfsSyncMemoryResourceImpl.pas"]),
    ("10-ui", ["UiComCtrls.pas", "UiTextEditor.pas", "UiUtils.pas", "UiMapTreeView.pas",
               "UiSpecCtrls.pas", "UiDropCtrls.pas", "UiActionTree.pas", "UiAutoComplete.pas",
               "UiCodePageEdit.pas", "UiEdits.pas", "UiHexEditor.pas", "UiListTable.pas",
               "UiMainControl.pas", "UiSpeedBar.pas", "UiSpeedHeader.pas", "UiTabFooter.pas",
               "UiTabHeader.pas", "UiTableEditor.pas", "UiThemes.pas", "UiThumb.pas",
               "UiVirtualListBox.pas", "UiWebBrowser.pas"]),
]

functions = attr["functions"]
already: set[str] = {f.stem for f in (ROOT / "pseudocode").glob("*.c")}

manifest = {"phases": {}, "total": 0, "done": 0, "missing_units": []}
for phase_name, units in PHASES:
    items: list[str] = []
    missing = [u for u in units if u not in by_unit_map] if (by_unit_map := {}) else []
    for unit in units:
        unit_path = unit_to_path.get(unit)
        if unit_path is None or "ThirdParty" in unit_path:
            continue
        for addr, info in functions.items():
            if info.get("unit") == unit and addr not in already:
                items.append(f"{addr}\t{unit}")
    items = sorted(set(items))
    batch_no = 0
    phase_files = []
    for start in range(0, len(items), 400):
        batch_no += 1
        target = QUEUE / f"{phase_name}-batch{batch_no:02d}.txt"
        target.write_text("\n".join(items[start:start + 400]) + "\n", encoding="utf-8")
        phase_files.append(target.name)
    manifest["phases"][phase_name] = {"units": units, "count": len(items), "batches": phase_files}
    manifest["total"] += len(items)
    print(f"{phase_name:<16} {len(items):>6} 个函数  ({len(phase_files)} 批)")

(QUEUE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n总工作量: {manifest['total']:,} 个待反编译（已完成 {len(already)} 个）")
print(f"工作队列: {QUEUE}")
