# BCompare UI 命令面（由 TPF0 资源解码）

- 表单数：211（完整解析 211）
- 对象总数：3641

## 动作表（15 个）

### TBCACTIONS — 48 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `MacCommandLineToolsAction` | Install Command Line Tools... | Install Command Line Tools\|Places bcomp and bcompare in /usr/local/bi |
| `SessionNewListAction` | &New Session | New Session\|Opens empty session of picked type in new view. |
| `TabNewAction` | New &Tab | New Tab\|Opens Home view in new tab. |
| `WindowNewAction` | New &Window | New Window\|Opens Home view in new window. |
| `SessionOpenAction` | &Open Session | Open Session\|Opens Home in new view. |
| `WorkspaceLoadListAction` | Load Wor&kspace | Load Workspace\|Restores picked saved view configuration. |
| `WorkspaceManagerAction` | Manage Workspaces... | Manage Workspaces\|Manages the saved view configurations that can be r |
| `WorkspaceSaveAsAction` | Sa&ve Workspace As... | Save Workspace As\|Stores current view configuration. |
| `CloseTabAction` | Close Tab | Close Tab\|Closes active tab. |
| `ExitAction` | E&xit | Exit\|Quits the application, prompts to save edits. |
| `UndoAction` |  | Undo\|Undoes previous action. |
| `RedoAction` |  | Redo\|Redoes previously undone action. |
| `CutAction` | Cu&t | Cut\|Cuts selection and puts it on Clipboard. |
| `CopyAction` | &Copy | Copy\|Copies selection and puts it on Clipboard. |
| `PasteAction` | &Paste | Paste\|Inserts Clipboard contents. |
| `SelectAllAction` | Select &All | Select All\|Selects all visible items. |
| `ProgramOptionsAction` | &Options... | Options\|Sets global preferences. |
| `FileFormatManagerAction` | File &Formats... | File Formats\|Manages file formats. |
| `ProfileManagerAction` | &Profiles... | Profiles\|Manages profiles. |
| `SourceControlManagerAction` | Source Co&ntrol Integration... | Source Control Integration\|Manages integration with version control s |
| `ExportAction` | &Export Settings... | Export Settings\|Saves user settings as a file. |
| `ImportAction` | &Import Settings... | Import Settings\|Loads user settings from a file. |
| `RestoreAction` | &Restore Factory Defaults... | Restore Factory Defaults\|Loads factory default settings. |
| `SaveSnapshotAction` | Save Snaps&hot... | Save Snapshot\|Saves details of specified folder for future comparison |
| `EditTextFileAction` | E&dit Text File | Edit Text File\|Opens new Text Edit view. |
| `ViewPatchAction` | View P&atch... | View Patch\|Opens picked patch file in new Text Patch view. |
| `DebugListAction` |  |  |
| `DebugIdentifyControlAction` |  |  |
| `DebugRaiseExceptionAction` |  |  |
| `MacWindowMinimizeAction` | Minimize | Minimize\|Minimizes active window. |
| `MacWindowMinimizeAllAction` | Minimize All | Minimize All\|Minimizes all application windows. |
| `MacWindowZoomAction` | Zoom | Zoom\|Maximizes or restores active window. |
| `MacWindowZoomAllAction` | Zoom All | Zoom All\|Maximizes all visible document windows. |
| `MacWindowNextAction` | Cycle Through Windows | Cycle Through Windows\|Selects window after active one. |
| `MacWindowPrevAction` | Cycle Back Through Windows | Cycle Back Through Windows\|Selects window before active one. |
| `TabNextAction` |  | Select Next Tab\|Selects tab after active one. |
| `TabPrevAction` |  | Select Previous Tab\|Selects tab before active one. |
| `MacTabToWindowAction` | Move Tab to New Window | Move Tab to New Window\|Removes active tab and makes it into new windo |
| `MacWindowMergeAllAction` | Merge All Windows | Merge All Windows\|Moves all tabs onto active window. |
| `MacWindowActivateAllAction` | Bring All to Front | Bring All to Front\|Brings all windows to the foreground. |
| `MacWindowArrangeAllAction` | Arrange in Front | Arrange in Front\|Arranges all visible windows. |
| `HelpContentsAction` | &Contents | Contents\|Shows help file. |
| `ContextHelpAction` | Context Sensitive &Help | Context Sensitive Help\|Shows context sensitive help for the active wi |
| `VisitSiteAction` | Scooter Software on the &Web | Scooter Software on the Web\|Opens the Scooter Software website in you |
| `CheckForUpdatesAction` | Check for &Updates | Check for Updates\|Checks our website to see if a newer version is ava |
| `SupportAction` | &Support | Support\|Displays Scooter Software contact information. |
| `EnterKeyAction` | &Enter Key... | Enter Key\|Enter registration key. |
| `AboutAction` | &About %s | About %s\|Displays program information, version number and copyright. |

### TDIRACTIONS — 116 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `ExpandAction` |  |  |
| `CollapseAction` |  |  |
| `ExpandSubfoldersAction` |  |  |
| `CollapseSubfoldersAction` |  |  |
| `NameFilterEditAction` |  | Name Filters Edit\|Focuses on edit listing current name file filters. |
| `NameFilterAction` |  | Name Filters\|Edits name file filters. |
| `SpecsBackAction` | Back | Back\|Changes to previous base folders. |
| `SpecsForwardAction` | Forward | Forward\|Changes to next base folders. |
| `UpOneLevelListAction` | Up One Level | Up One Level\|Changes base folders on picked sides to their parent fol |
| `UpOneLevelLeftAction` | &Left Side | Up One Level on Left Side\|Changes left base folder to its parent fold |
| `UpOneLevelCenterAction` | &Center Side | Up One Level on Center Side\|Changes center base folder to its parent  |
| `UpOneLevelRightAction` | &Right Side | Up One Level on Right Side\|Changes right base folder to its parent fo |
| `UpOneLevelOutputAction` | &Output Side | Up One Level on Output Side\|Changes output base folder to its parent  |
| `UpOneLevelAllAction` |  |  |
| `MergeBaseViewAction` | &Merge Base Folders | Merge Base Folders\|Merges base folders in new view. |
| `SyncBaseViewAction` | S&ync Base Folders | Sync Base Folders\|Synchronizes base folders in new view. |
| `CompareToOutputListAction` | Compare to O&utput | Compare to Output\|Compares picked side and output in new view. |
| `CompareLeftToOutputAction` | &Left Side | Compare Left to Output\|Compares left and output in new view. |
| `CompareCenterToOutputAction` | &Center Side | Compare Center to Output\|Compares center and output in new view. |
| `CompareRightToOutputAction` | &Right Side | Compare Right to Output\|Compares right and output in new view. |
| `QuickCompareAction` | &Quick Compare | Quick Compare\|Quick compare selected files. |
| `CompareToAction` | Compare To... | Compare To\|Marks item for comparing in new view. |
| `AlignWithAction` |  | Align With\|Marks item for manual realignment. |
| `CompareAction` | &Compare Contents | Compare Contents\|Determines overall comparison state for selected ite |
| `MergeAction` | &Merge... | Merge\|Performs automated merge of selected items. |
| `CopyRightAction` | Cop&y to Right | Copy to Right\|Copies selected items from left to right. |
| `CopyLeftAction` | Cop&y to Left | Copy to Left\|Copies selected items from right to left. |
| `CopyPromptAction` | Cop&y to Side... | Copy to Side\|Prompts which side to copy selected items to. |
| `CopySideAction` |  | Copy to Other Side\|Copies selected items to other side. |
| `CopyToOutputAction` | Cop&y to Output... | Copy to Output\|Copies selected items to output folder. |
| `MoveRightAction` | &Move to Right | Move to Right\|Moves selected items from left to right. |
| `MoveLeftAction` | &Move to Left | Move to Left\|Moves selected items from right to left. |
| `MovePromptAction` | &Move to Side... | Move to Side\|Prompts which side to move selected items to. |
| `MoveSideAction` |  | Move to Other Side\|Moves selected items to other side. |
| `MoveBothAction` | Exchange | Exchange\|Moves selected items to other side. |
| `CopyToAction` | Copy to &Folder... | Copy to Folder\|Copies selected items to another folder. |
| `MoveToAction` | Mo&ve to Folder... | Move to Folder\|Moves selected items to another folder. |
| `DeleteAction` | &Delete | Delete\|Deletes selected items. |
| `PermanentDeleteAction` |  | Delete Permanently\|Deletes selected items without moving them to the  |
| `RenameAction` | &Rename | Rename\|Renames selected items. |
| `AttributesAction` | &Attributes... | Attributes\|Sets the DOS attributes of selected files. |
| `TouchAction` | &Touch... | Touch\|Sets timestamps of selected items. |
| `NewFolderAction` | &New Folder... | New Folder\|Creates a new folder. |
| `IgnoredAction` | I&gnored | Ignored\|Ignores or unignores differences in selected items. |
| `FileReportAction` | File Compare Re&port... | File Compare Report\|Produces file comparison report. |
| `SyncListAction` | Synchroni&ze | Synchronize\|Synchronizes by picked method. |
| `UpdateRightAction` | Update &Right... | Update Right\|Synchronizes by copying newer and orphan items from left |
| `UpdateLeftAction` | Update &Left... | Update Left\|Synchronizes by copying newer and orphan items from right |
| `UpdateBothAction` | Update &Both... | Update Both\|Synchronizes by copying newer and orphan items from left  |
| `MirrorRightAction` | Mirror to Ri&ght... | Mirror to Right\|Synchronizes by replacing all different items on righ |
| `MirrorLeftAction` | Mirror to Le&ft... | Mirror to Left\|Synchronizes by replacing all different items on left, |
| `SourceControlListAction` | So&urce Control | Source Control\|Performs picked source control command. |
| `VcsAddAction` | &Add to Source Control | Add to Source Control\|Adds selected items to source control. |
| `VcsRemoveAction` | &Remove from Source Control | Remove from Source Control\|Removes selected items from source control |
| `VcsGetLatestAction` | Get Latest &Version | Get Latest Version\|Gets latest version of items from source control. |
| `VcsGetAction` | &Get... | Get\|Gets particular version of items from source control. |
| `VcsCheckInAction` | Check &In... | Check In\|Checks item into source control. |
| `VcsCheckOutAction` | Check &Out | Check Out\|Checks out item from source control. |
| `VcsUndoCheckOutAction` | &Undo Check Out | Undo Check Out\|Undoes checkout from source control. |
| `VcsDiffAction` | Show &Differences | Show Differences\|Shows source control differences. |
| `VcsHistoryAction` | Show &History | Show History\|Shows source control history. |
| `VcsPropertiesAction` | Show &Properties | Show Properties\|Shows source control properties. |
| `VcsRunAppAction` | Ru&n Source Control Application | Run Source Control Application\|Runs source control application. |
| `SelectAllFilesAction` | Select All &Files | Select All Files\|Selects all visible files. |
| `SelectNewerListAction` | Select &Newer | Select Newer\|Selects all newer files on picked sides. |
| `SelectNewerLeftAction` | &Left Side | Select Left Newer\|Selects all newer files on the left. |
| `SelectNewerRightAction` | &Right Side | Select Right Newer\|Selects all newer files on the right. |
| `SelectNewerBothAction` | &Both Sides | Select Both Newer\|Selects all newer files on both sides. |
| `SelectOrphanListAction` | Select &Orphans | Select Orphans\|Selects all orphan files on picked sides. |
| `SelectOrphanLeftAction` | &Left Side | Select Left Orphans\|Selects all orphan files on the left. |
| `SelectOrphanRightAction` | &Right Side | Select Right Orphans\|Selects all orphan files on the right. |
| `SelectOrphanBothAction` | &Both Sides | Select Both Orphans\|Selects all orphan files on both sides. |
| `DiffNextAction` | &Next Difference | Next Difference\|Positions at next difference. |
| `DiffPrevAction` | &Previous Difference | Previous Difference\|Positions at previous difference. |
| `FavCompareAllAction` | Show All | Show All\|Shows same, left orphan, right orphan, left newer, right new |
| `FavDiffAction` | Show Differences | Show Differences\|Shows left orphan, right orphan, left newer, right n |
| `FavSameAction` | Show Same | Show Same\|Shows same items. |
| `FavNoOrphanAction` | Show No Orphans | Show No Orphans\|Shows same, left newer, right newer and difference it |
| `FavDiffNoOrphanAction` | Show Differences but No Orphans | Show Differences but No Orphans\|Shows left newer, right newer and dif |
| `FavOrphanAction` | Show Orphans | Show Orphans\|Shows left orphan and right orphan items. |
| `FavLeftNewerAction` | Show Left Newer | Show Left Newer\|Shows left newer items. |
| `FavRightNewerAction` | Show Right Newer | Show Right Newer\|Shows right newer items. |
| `FavLeftNewerOrphanAction` | Show Left Newer and Left Orphans | Show Left Newer and Left Orphans\|Shows left orphan and left newer ite |
| `FavRightNewerOrphanAction` | Show Right Newer and Right Orphans | Show Right Newer and Right Orphans\|Shows right orphan and right newer |
| `FavLeftOrphanAction` | Show Left Orphans | Show Left Orphans\|Shows left orphan items. |
| `FavRightOrphanAction` | Show Right Orphans | Show Right Orphans\|Shows right orphan items. |
| `FavCompareNoneAction` | Show None | Show None\|Hides all files. |
| `FavMergeAllAction` | Show All | Show All\|Shows unchanged, same change, left add, right add, left dele |
| `FavChangedAction` | Show Changes | Show Changes\|Shows left add, right add, left delete, right delete, le |
| `FavConflictAction` | Show Conflicts | Show Conflicts\|Shows conflict items. |
| `FavLeftAction` | Show Left Changes | Show Left Changes\|Shows left add, left delete and left change items. |
| `FavRightAction` | Show Right Changes | Show Right Changes\|Shows right add, right delete and right change ite |
| `FavMergeableAction` | Show Mergeable | Show Mergeable\|Shows same change and difference change items. |
| `FavUnchangedAction` | Show Unchanged | Show Unchanged\|Shows unchanged items. |
| `FavMergeNoneAction` | Show None | Show None\|Shows no items. |
| `TogSameAction` |  | Toggle Same\|Shows or hides same items. |
| `TogLeftOrphanAction` |  | Toggle Left Orphans\|Shows or hides left orphan items. |
| `TogRightOrphanAction` |  | Toggle Right Orphans\|Shows or hides right orphan items. |
| `TogLeftNewerAction` |  | Toggle Left Newer\|Shows or hides left newer items. |
| `TogRightNewerAction` |  | Toggle Right Newer\|Shows or hides right newer items. |
| `TogDiffAction` |  | Toggle Differences\|Shows or hides difference items. |
| `TogNoModAction` |  | Toggle Unchanged\|Shows or hides unchanged items. |
| `TogSameModAction` |  | Toggle Same Changes\|Shows or hides same change items. |
| `TogLeftAddAction` |  | Toggle Left Adds\|Shows or hides left add items. |
| `TogRightAddAction` |  | Toggle Right Adds\|Shows or hides right add items. |
| `TogLeftDelAction` |  | Toggle Left Deletes\|Shows or hides left delete items. |
| `TogRightDelAction` |  | Toggle Right Deletes\|Shows or hides right delete items. |
| `TogLeftModAction` |  | Toggle Left Changes\|Shows or hides left change items. |
| `TogRightModAction` |  | Toggle Right Changes\|Shows or hides right change items. |
| `TogDiffModAction` |  | Toggle Mergeable\|Shows or hides mergeable items. |
| `TogConflictAction` |  | Toggle Conflicts\|Shows or hides conflict items. |
| `DirShowAllAction` | &Always Show Folders | Always Show Folders\|Shows all folders, ignoring the display filter. |
| `DirCompareStructureAction` | Compare Files and Fol&der Structure | Compare Files and Folder Structure\|Shows folders if they, or items th |
| `DirCompareFilesOnlyAction` | Only Compare &Files | Only Compare Files\|Shows folders only if they contain files matching  |
| `DirFlattenAction` | &Ignore Folder Structure | Ignore Folder Structure (Flatten)\|Compares all files as if they were  |
| `ShowCenterAction` | Ce&nter Pane | Center Pane\|Shows or hides center pane. |

### TDIRBASEACTIONS — 36 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `SelectAllAction` |  |  |
| `SwapAction` |  | Swap Sides\|Exchanges left, right base folders. |
| `BrowseListAction` | B&rowse for Folder | Browse for Folder\|Browses for an existing folder on picked side. |
| `BrowseLeftAction` | &Left Side | Browse for Folder on Left Side\|Browses for an existing folder on left |
| `BrowseCenterAction` | &Center Side | Browse for Folder on Center Side\|Browses for an existing folder on ce |
| `BrowseRightAction` | &Right Side | Browse for Folder on Right Side\|Browses for an existing folder on rig |
| `BrowseOutputAction` | &Output Side | Browse for Folder on Output Side\|Browses for an existing folder on ou |
| `StopAction` |  | Stop Loading\|Terminates comparison. |
| `ExpandAction` | Open Folder | Open Folder\|Opens selected folder. |
| `CollapseAction` | Close Folder | Close Folder\|Closes selected folder. |
| `ExpandSubfoldersAction` | Open Subfolders | Open Subfolders\|Opens selected folders and all their subfolders. |
| `CollapseSubfoldersAction` | Close Subfolders | Close Subfolders\|Closes selected folders and their subfolders. |
| `SetAsBaseFoldersAction` |  | Set as Base Folders\|Sets selected folders as base folders. |
| `SetAsOtherBaseFolderAction` | Set as Base on Ot&her Side | Set as Base on Other Side\|Sets selected folder as base folder on othe |
| `OpenAction` |  | Open\|Opens selected items in new view. |
| `OpenWithListAction` | Open &With | Open With\|Opens selected items in new view of picked type. |
| `AssocAppAction` | Associated Application | Associated Application\|Opens selected items with associated applicati |
| `RevealInFinderAction` | Reveal in Finder | Reveal in Finder\|Shows Finder and selects the picked file. |
| `ExcludeAction` | &Exclude | Exclude\|Filters selected items to remove them from comparison. |
| `CopyFilenamesAction` | Copy F&ilename | Copy Filename\|Copies selected items' paths to Clipboard. |
| `RefreshSelectionAction` | Refresh &Selection | Refresh Selection\|Refreshes selected items. |
| `ExplorerListAction` | E&xplorer | Explorer\|Shows Windows Explorer context menu for selected items. |
| `ExpandAllAction` | &Expand All | Expand All\|Opens all folders. |
| `CollapseAllAction` | &Collapse All | Collapse All\|Closes all folders. |
| `SelectInvertAction` | &Invert Selection | Invert Selection\|Selects all items not currently selected, and desele |
| `RefreshAction` | &Refresh | Refresh\|Refreshes open folders. |
| `FullRefreshAction` | F&ull Refresh | Full Refresh\|Refreshes entire comparison. |
| `ExistsNextAction` |  | Next Existing Filename\|Positions at next filename, skipping over gaps |
| `ExistsPrevAction` |  | Previous Existing Filename\|Positions at previous filename, skipping o |
| `FindFilenameAction` | &Find Filename... | Find Filename\|Finds filename matching search string. |
| `FindFilenameNextAction` | Find Ne&xt Filename | Find Next Filename\|Finds next filename matching search string. |
| `FindFilenamePrevAction` | Find Pre&vious Filename | Find Previous Filename\|Finds previous filename matching search string |
| `SuppressFiltersAction` | &Suppress Filters | Suppress Filters\|Temporarily suppresses display and file filters. |
| `ColListAction` | &Columns | Columns\|Shows or hides picked column. |
| `LegendAction` | &Legend | Legend\|Shows or hides legend window. |
| `ShowLogAction` | L&og | Log\|Shows or hides log panel. |

### TDIRSYNCACTIONS — 9 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `RunAction` |  | Run Sync\|Performs all sync operations. |
| `CompareBaseViewAction` | Co&mpare Base Folders | Compare Base Folders\|Compares base folders in new view. |
| `SyncLeaveAction` | Lea&ve Alone | Leave Alone\|Changes sync operation to leave alone. |
| `SyncCopyLeftAction` | Copy Right to &Left | Copy Right to Left\|Changes sync operation to copy right to left. |
| `SyncCopyRightAction` | Copy Left to &Right | Copy Left to Right\|Changes sync operation to copy left to right. |
| `SyncDeleteLeftAction` | Delete Le&ft | Delete Left\|Changes sync operation to delete left. |
| `SyncDeleteRightAction` | Delete Ri&ght | Delete Right\|Changes sync operation to delete right. |
| `ConflictNextAction` | &Next Conflict | Next Conflict\|Positions at next conflict. |
| `ConflictPrevAction` | &Previous Conflict | Previous Conflict\|Positions at previous conflict. |

### TFILEACTIONS — 54 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `FileFormatAction` |  | Format\|Edits current File Format. |
| `ReloadAction` | &Reload Files | Reload Files\|Reloads displayed files. |
| `RecompareAction` | Reco&mpare Files | Recompare Files\|Recompares displayed files without reloading them. |
| `CompareUsingViewListAction` | Compare Files &Using | Compare Files Using\|Compares files in picked new view. |
| `MergeViewAction` | Mer&ge Files | Merge Files\|Merges files in new view. |
| `CompareToOutputListAction` | Compare to O&utput | Compare to Output\|Compares picked side and output in new view. |
| `CompareLeftToOutputAction` | &Left Side | Compare Left to Output\|Compares left and output in new view. |
| `CompareCenterToOutputAction` | &Center Side | Compare Center to Output\|Compares center and output in new view. |
| `CompareRightToOutputAction` | &Right Side | Compare Right to Output\|Compares right and output in new view. |
| `OpenAction` | &Open File... | Open File\|Opens existing file into picked pane. |
| `OpenLocalAction` | Open File on File S&ystem... | Open File on File System\|Opens existing local file into picked pane. |
| `OpenProfileAction` | Open File Using &Profile... | Open File Using Profile\|Opens existing file into picked pane using pr |
| `OpenClipboardAction` | Open &Clipboard | Open Clipboard\|Opens Clipboard contents into picked pane. |
| `OpenWithListAction` | Open &With | Open With\|Opens picked file with picked application. |
| `AssocAppAction` | Associated Application | Associated Application\|Opens picked file with associated application. |
| `RevealInFinderAction` | Reveal in Finder | Reveal in Finder\|Shows Finder and selects the picked file. |
| `SaveAction` | &Save File | Save File\|Saves picked file which has been modified. |
| `SaveAsAction` | Save File &As... | Save File As\|Saves picked file with new name. |
| `SaveAsLocalAction` | Save File on Fi&le System As... | Save File on File System As\|Saves picked file with new name on file s |
| `SaveAsProfileAction` | Save File Using Pro&file As... | Save File Using Profile As\|Saves picked file with new name using prof |
| `ExplorerListAction` | E&xplorer | Explorer\|Shows Windows Explorer context menu for picked file. |
| `DiffItemNextAction` | &Next Difference Item | Next Difference Item\|Positions at next difference item. |
| `DiffItemPrevAction` | &Previous Difference Item | Previous Difference Item\|Positions at previous difference item. |
| `DiffFileNextAction` | Next D&ifference Files | Next Difference Files\|Opens folder compare's next difference files. |
| `DiffFilePrevAction` | Previ&ous Difference Files | Previous Difference Files\|Opens folder compare's previous difference  |
| `CopyFileRightAction` | &Copy File to Right and Open Next Difference | Copy File to Right and Open Next Difference\|Copies left file to right |
| `CopyFileLeftAction` | Cop&y File to Left and Open Next Difference | Copy File to Left and Open Next Difference\|Copies right file to left  |
| `TakeFileLeftAction` | Take Left File and Open Next Difference | Take Left File and Open Next Difference\|Takes left file and opens fol |
| `TakeFileRightAction` | Take Right File and Open Next Difference | Take Right File and Open Next Difference\|Takes right file and opens f |
| `ExistsNextAction` |  | Next Existing Item\|Positions at next item, skipping over gaps. |
| `ExistsPrevAction` |  | Previous Existing Item\|Positions at previous item, skipping over gaps |
| `FindAction` | &Find... | Find\|Finds search string. |
| `FindNextAction` | Find Ne&xt | Find Next\|Finds next occurrence of search string. |
| `FindPrevAction` | Find Pre&vious | Find Previous\|Finds previous occurrence of search string. |
| `GoLeftAction` |  | Go Left\|Positions in pane left of current one. |
| `GoRightAction` |  | Go Right\|Positions in pane right of current one. |
| `GoNextAction` |  | Go Next\|Positions in pane after current one. |
| `GoPrevAction` |  | Go Prev\|Positions in pane before current one. |
| `FavCompareAllAction` | Show All | Show All\|Shows same, left orphan, right orphan and difference items. |
| `FavDiffAction` | Show Differences | Show Differences\|Shows left orphan, right orphan and difference items |
| `FavSameAction` | Show Same | Show Same\|Shows same items. |
| `FavCompareNoneAction` | Show None | Show None\|Shows no items. |
| `TogSameAction` |  | Toggle Same\|Shows or hides same items. |
| `TogLeftOrphanAction` |  | Toggle Left Orphans\|Shows or hides left orphan items. |
| `TogRightOrphanAction` |  | Toggle Right Orphans\|Shows or hides right orphan items. |
| `TogDiffAction` |  | Toggle Differences\|Shows or hides difference items. |
| `ShowWSAction` | Visible &Whitespace | Visible Whitespace\|Shows or hides visible spaces, tabs. |
| `DisplayFontAction` | Display &Font... |  |
| `DisplayFontIncreaseAction` | Increase Display Font Size |  |
| `DisplayFontDecreaseAction` | Decrease Display Font Size |  |
| `DisplayFontResetAction` | Reset Display Font Size |  |
| `SideBySideAction` | &Side-by-Side Layout | Side-by-Side Layout\|Arranges panes left and right of each other. |
| `OverUnderAction` | &Over-Under Layout | Over-Under Layout\|Arranges panes above and below each other. |
| `ShowSpecInfoAction` | File &Info | File Info\|Shows or hides file information. |

### THEXACTIONS — 22 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `SelectAllAction` |  | Select All\|Selects all visible bytes. |
| `FileFormatAction` |  |  |
| `DiffItemNextAction` | &Next Difference Bytes | Next Difference Bytes\|Positions at next difference bytes. |
| `DiffItemPrevAction` | &Previous Difference Bytes | Previous Difference Bytes\|Positions at previous difference bytes. |
| `ExistsNextAction` |  | Next Existing Byte\|Positions at next existing byte, skipping over gap |
| `ExistsPrevAction` |  | Previous Existing Byte\|Positions at previous existing byte, skipping  |
| `FavCompareAllAction` |  | Show All\|Shows same, left orphan, right orphan and difference bytes. |
| `FavDiffAction` |  | Show Differences\|Shows left orphan, right orphan and difference bytes |
| `FavSameAction` |  | Show Same\|Shows same bytes. |
| `CopyRightAction` | Cop&y to Right | Copy to Right\|Copies selected or current bytes to right pane. |
| `CopyLeftAction` | Cop&y to Left | Copy to Left\|Copies selected or current bytes to left pane. |
| `CopySideAction` |  | Copy to Other Side\|Copies selected or current bytes to pane on other  |
| `DeleteAction` | &Delete | Delete\|Deletes selection. |
| `ReplaceAction` | &Replace... | Replace\|Replaces search string. |
| `GoToAction` | &Go To... | Go To\|Positions at specified byte. |
| `ItemNumAction` |  | Current Byte Address\|Copies current byte address and puts it on Clipb |
| `LittleEndianListAction` | &Little Endian Values | Little Endian Values\|Displays little endian values in picked way. |
| `BigEndianListAction` | &Big Endian Values | Big Endian Values\|Displays big endian values in picked way. |
| `ShowItemNumAction` | Byte &Addresses | Byte Addresses\|Shows or hides byte addresses. |
| `LayoutAction` | La&yout... | Layout\|Configures layout options. |
| `ShowThumbnailAction` | Thu&mbnail | Thumbnail\|Shows or hides thumbnail view. |
| `OverwritingAction` |  | Overwrite\|Typing replaces bytes instead of inserting them. |

### THOMEACTIONS — 4 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `FindAction` |  | Find\|Finds search string. |
| `ShowManageAction` | Show Session &Management | Show Session Management\|Shows or hides management panel. |
| `MaximizeManageAction` | Ma&ximize Session Management | Maximize Session Management\|Maximizes or restores management panel. |
| `ShowWebAction` | Show &Web Resources | Show Web Resources\|Shows or hides web panel. |

### TMEDIAACTIONS — 4 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `Play2Action` |  | Play Both\|Plays both audio tracks. |
| `PlayAction` |  | Play\|Plays audio track. |
| `IsSigAction` |  | Item Is Important\|Marks selected item as important or unimportant. |
| `ShowDetailsAction` | Text &Details | Text Details\|Shows or hides text details panel. |

### TPIXACTIONS — 20 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `FileFormatAction` |  |  |
| `DisplayFontIncreaseAction` |  |  |
| `DisplayFontDecreaseAction` |  |  |
| `DiffToleranceAction` | To&lerance Mode | Tolerance Mode\|Detects pixel differences greater than configurable to |
| `DiffRangeAction` | Mismatch Ran&ge Mode | Mismatch Range Mode\|Measures degree of pixel difference. |
| `DiffBlendAction` | &Blend Mode | Blend Mode\|Blends pictures based on configurable percentage. |
| `AutoScaleAction` | Auto S&cale | Auto Scale\|Makes smaller picture as large as other picture. |
| `RotateRightAction` | Rotate Cloc&kwise | Rotate Clockwise\|Spins current picture to right by 90 degrees. |
| `RotateLeftAction` | Rotate Cou&nterclockwise | Rotate Counterclockwise\|Spins current picture to left by 90 degrees. |
| `FlipHorzAction` | Flip &Horizontally | Flip Horizontally\|Swaps pixels of current picture relative to its hor |
| `FlipVertAction` | Flip &Vertically | Flip Vertically\|Swaps pixels of current picture relative to its verti |
| `OffsetResetAction` | &Reset Difference Offset | Reset Difference Offset\|Realigns top left corner of both pictures. |
| `CompareTagsAction` | Compare &Metadata | Compare Metadata\|Compares and shows metadata. |
| `BlendToggleAction` | Blend T&oggle | Blend Toggle\|Switches between left and right pictures. |
| `FullScreenAction` | Full Scr&een | Full Screen\|Makes current picture show as large as possible. |
| `ZoomListAction` | &Zoom | Zoom\|Makes picture appear to change size in picked way. |
| `ZoomInAction` | Zoom &In | Zoom In\|Makes pictures appear to be larger. |
| `ZoomOutAction` | Zoom &Out | Zoom Out\|Makes pictures appear to be smaller. |
| `ZoomActualAction` | &Actual Size | Actual Size\|Makes pictures appear in their actual size. |
| `ZoomFitAction` | &Fit to Window | Fit to Window\|Makes pictures appear to fill panes. |

### TREGACTIONS — 29 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `SwapAction` |  | Swap Sides\|Exchanges left, right registries. |
| `ReloadAction` | &Reload | Reload\|Reloads displayed registries. |
| `RecompareAction` | Reco&mpare | Recompare\|Recompares displayed registries without reloading them. |
| `OpenAction` | &Open... | Open\|Opens registry into picked pane. |
| `OpenLocalAction` | Open Registry File on File S&ystem... | Open Registry File on File System\|Opens existing local registry file  |
| `OpenProfileAction` | Open Registry File Using &Profile... | Open Registry File Using Profile\|Opens existing registry file into pi |
| `UpOneLevelListAction` | Up One Level | Up One Level\|Changes base keys on picked sides to their parent keys. |
| `UpOneLevelLeftAction` | &Left Side | Up One Level on Left Side\|Changes left base key to its parent key. |
| `UpOneLevelRightAction` | &Right Side | Up One Level on Right Side\|Changes right base key to its parent key. |
| `UpOneLevelBothAction` | &Both Sides | Up One Level on Both Sides\|Changes both base keys to their parent key |
| `OpenRegAction` | Open &Registry... | Open Registry\|Opens live registry into picked pane. |
| `SetAsBasesAction` |  | Set as Base Keys\|Sets selected keys as base keys. |
| `SetBothAsBasesAction` | Set B&oth as Base Keys | Set Both as Base Keys\|Sets selected key and key on other side as base |
| `SetAsOtherBaseAction` | Set as Base Key on Ot&her Side | Set as Base Key on Other Side\|Sets selected key as base key on other  |
| `CopyRightAction` | Cop&y to Right | Copy to Right\|Copies selected items to right pane. |
| `CopyLeftAction` | Cop&y to Left | Copy to Left\|Copies selected items to left pane. |
| `CopySideAction` |  | Copy to Other Side\|Copies selected items to pane on other side. |
| `DeleteAction` | &Delete | Delete\|Deletes selected items. |
| `RenameAction` | Re&name | Rename\|Renames item. |
| `NewKeyAction` | New &Key | New Key\|Adds a new key. |
| `NewValAction` | New &Value | New Value\|Adds a new value. |
| `ModifyAction` | &Modify... | Modify\|Modifies value. |
| `CopyKeyNameAction` | &Copy Key Name | Copy Key Name\|Copies key's name to Clipboard. |
| `ExportKeyAction` | &Export... | Export\|Saves key as registry file. |
| `ExportAllAction` | Export A&ll... | Export All\|Saves all keys as registry file. |
| `ExpandAllAction` | &Expand All | Expand All\|Opens all items. |
| `CollapseAllAction` | &Collapse All | Collapse All\|Closes all items. |
| `ShowTextDetailsAction` | Text &Details | Text Details\|Shows or hides text details panel. |
| `ShowHexDetailsAction` | He&x Details | Hex Details\|Shows or hides hexadecimal details panel. |

### TSESSIONACTIONS — 16 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `SessionHomeAction` |  | Home\|Replaces current view with Home view. |
| `SessionsComboAction` |  | Sessions Button\|Focuses on dropdown button listing sessions that can  |
| `SessionSaveAction` | &Save Session | Save Session\|Saves this session. |
| `SessionSaveAsAction` | Save Session &As... | Save Session As\|Saves this session with new name. |
| `SessionEditAction` | S&ession Settings... | Session Settings\|Edits current session settings. |
| `SessionLockedAction` | &Locked | Locked\|Locks or unlocks current session. |
| `SessionClearAction` | &Clear Session | Clear Session\|Replaces current view with empty session. |
| `RulesAction` |  | Rules\|Edits current Rules definitions. |
| `SwapAction` | Swap Si&des | Swap Sides\|Exchanges left, right files. |
| `ReportAction` | %s Re&port... | %0:s Report\|Produces %0:s report. |
| `InfoAction` | %s &Info | %0:s Info\|Displays %0:s statistics. |
| `CompareParentsAction` | Compare Parent &Folders | Compare Parent Folders\|Compares folders containing current items in n |
| `MergeParentsAction` | Merge Parent &Folders | Merge Parent Folders\|Merges folders containing current items in new v |
| `InsigIgnoredAction` | Ignore &Unimportant Differences | Ignore Unimportant Differences\|Treats unimportant differences as same |
| `SameModIgnoredAction` | Ignore S&ame Changes | Ignore Same Changes\|Treats same changes as same. |
| `ShowToolbarAction` | &Toolbar | Toolbar\|Shows or hides toolbar. |

### TTABLEACTIONS — 43 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `SelectAllAction` |  | Select All\|Selects all visible rows. |
| `FileFormatAction` |  |  |
| `DiffItemNextAction` | &Next Difference Row | Next Difference Row\|Positions at next difference row. |
| `DiffItemPrevAction` | &Previous Difference Row | Previous Difference Row\|Positions at previous difference row. |
| `ExistsNextAction` |  | Next Existing Row\|Positions at next existing row, skipping over gaps. |
| `ExistsPrevAction` |  | Previous Existing Row\|Positions at previous existing row, skipping ov |
| `FavCompareAllAction` |  | Show All\|Shows same, left orphan, right orphan and difference rows. |
| `FavDiffAction` |  | Show Differences\|Shows left orphan, right orphan and difference rows. |
| `FavSameAction` |  | Show Same\|Shows same rows. |
| `FavCompareNoneAction` |  | Show None\|Shows no rows. |
| `TogSameAction` |  | Toggle Same\|Shows or hides same rows. |
| `TogLeftOrphanAction` |  | Toggle Left Orphans\|Shows or hides left orphan rows. |
| `TogRightOrphanAction` |  | Toggle Right Orphans\|Shows or hides right orphan rows. |
| `TogDiffAction` |  | Toggle Differences\|Shows or hides difference rows. |
| `AlignWithAction` | Align &With... | Align With\|Marks selected rows for manual realignment. |
| `CopyRightAction` | Cop&y to Right | Copy to Right\|Copies selected rows to right pane. |
| `CopyLeftAction` | Cop&y to Left | Copy to Left\|Copies selected rows to left pane. |
| `CopySideAction` |  | Copy to Other Side\|Copies selected rows to pane on other side. |
| `CopyCellRightAction` | Cop&y Cells to Right | Copy Cells to Right\|Copies selected cells to right pane. |
| `CopyCellLeftAction` | Cop&y Cells to Left | Copy Cells to Left\|Copies selected cells to left pane. |
| `CopyCellSideAction` |  | Copy Cells to Other Side\|Copies selected cells to pane on other side. |
| `DeleteAction` | &Delete | Delete\|Deletes selection. |
| `DeleteItemAction` | &Delete Row | Delete Row\|Deletes selected rows. |
| `DeleteColAction` | &Delete Column | Delete Column\|Deletes selected columns. |
| `InsertItemBeforeAction` | Insert Row &Before | Insert Row Before\|Inserts new rows before selected ones. |
| `InsertItemAfterAction` | &Insert Row After | Insert Row After\|Inserts new rows after selected ones. |
| `InsertColBeforeAction` | Insert Column B&efore | Insert Column Before\|Inserts new columns before selected ones. |
| `InsertColAfterAction` | I&nsert Column After | Insert Column After\|Inserts new columns after selected ones. |
| `ModifyAction` | &Modify... | Modify\|Modifies cell text. |
| `SortAction` | &Sort... | Sort\|Sorts selected data. |
| `DiffNextAction` | Nex&t Difference Cell | Next Difference Cell\|Positions at next difference cell. |
| `DiffPrevAction` | Previo&us Difference Cell | Previous Difference Cell\|Positions at previous difference cell. |
| `DiffSheetNextAction` | Next Difference &Sheet | Next Difference Sheet\|Positions at next difference sheet. |
| `DiffSheetPrevAction` | Previous Difference S&heet | Previous Difference Sheet\|Positions at previous difference sheet. |
| `EditNextAction` | Next &Edit | Next Edit\|Positions at next edited text. |
| `EditPrevAction` | Previous E&dit | Previous Edit\|Positions at previous edited text. |
| `ReplaceAction` | &Replace... | Replace\|Replaces search string. |
| `GoToAction` | &Go To... | Go To\|Positions at specified row and column. |
| `ColHideSameAction` | &Hide Same Columns | Hide Same Columns\|Hides same columns. |
| `ColDetectSizeAction` | &Resize Columns to Fit | Resize Columns to Fit\|Makes columns wide enough for data to be fully  |
| `ShowItemNumAction` | Row &Numbers | Row Numbers\|Shows or hides row numbers. |
| `ShowThumbnailAction` | Thu&mbnail | Thumbnail\|Shows or hides thumbnail view. |
| `ShowDetailsAction` | Text &Details | Text Details\|Shows or hides text details panel. |

### TTEXTACTIONS — 112 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `SelectAllAction` |  | Select All\|Selects all visible lines. |
| `FileFormatAction` |  |  |
| `ExistsNextAction` |  | Next Existing Line\|Positions at next existing line, skipping over gap |
| `ExistsPrevAction` |  | Previous Existing Line\|Positions at previous existing line, skipping  |
| `FavCompareAllAction` |  | Show All\|Shows same, left orphan, right orphan and difference lines. |
| `FavDiffAction` |  | Show Differences\|Shows left orphan, right orphan and difference lines |
| `FavSameAction` |  | Show Same\|Shows same lines. |
| `FavCompareNoneAction` |  | Show None\|Shows no lines. |
| `TogSameAction` |  | Toggle Same\|Shows or hides same lines. |
| `TogLeftOrphanAction` |  | Toggle Left Orphans\|Shows or hides left orphan lines. |
| `TogRightOrphanAction` |  | Toggle Right Orphans\|Shows or hides right orphan lines. |
| `TogDiffAction` |  | Toggle Differences\|Shows or hides difference lines. |
| `CheckInAction` | Check &In... | Check In\|Checks file into source control. |
| `CheckOutAction` | Check Ou&t | Check Out\|Checks out file from source control. |
| `UndoCheckOutAction` | &Undo Check Out | Undo Check Out\|Undoes checkout from source control. |
| `ApplyPatchAction` | &Apply Patch | Apply Patch\|Applies patch file. |
| `AlignWithAction` | Align &With... | Align With\|Marks selected lines for manual realignment. |
| `IsolateAction` | I&solate | Isolate\|Realigns comparison so that selected lines are by themselves. |
| `ReplacementAction` | Replace&ment... | Replacement\|Adds item to replacement list based on current difference |
| `CopyRightAction` | Cop&y to Right | Copy to Right\|Copies selected lines or current section to right pane. |
| `CopyLeftAction` | Cop&y to Left | Copy to Left\|Copies selected lines or current section to left pane. |
| `CopySideAction` |  | Copy to Other Side\|Copies selected lines or current section to pane o |
| `CopyItemRightAction` | Cop&y Line to Right | Copy Line to Right\|Copies current line to right pane. |
| `CopyItemLeftAction` | Cop&y Line to Left | Copy Line to Left\|Copies current line to left pane. |
| `CopyItemSideAction` |  | Copy Line to Other Side\|Copies current line to pane on other side. |
| `ConflictAction` | &Conflict | Conflict\|Clears or sets conflict for selected lines or current sectio |
| `TakeLeftAction` | Ta&ke Left | Take Left\|Takes selected lines or current section from left pane. |
| `TakeCenterAction` | Ta&ke Center | Take Center\|Takes selected lines or current section from center pane. |
| `TakeRightAction` | Ta&ke Right | Take Right\|Takes selected lines or current section from right pane. |
| `TakeLeftRightAction` | Take Left Then Ri&ght | Take Left Then Right\|Takes selected lines or current section from lef |
| `TakeRightLeftAction` | Take Rig&ht Then Left | Take Right Then Left\|Takes selected lines or current section from rig |
| `TakeItemLeftAction` | Ta&ke Left Line | Take Left Line\|Takes current line from left pane. |
| `TakeItemCenterAction` | Ta&ke Center Line | Take Center Line\|Takes current line from center pane. |
| `TakeItemRightAction` | Ta&ke Right Line | Take Right Line\|Takes current line from right pane. |
| `IncreaseIndentAction` | I&ncrease Indent | Increase Indent\|Increases indentation of selected lines. |
| `DecreaseIndentAction` | D&ecrease Indent | Decrease Indent\|Decreases indentation of selected lines. |
| `DeleteAction` | &Delete | Delete\|Deletes selection. |
| `DeleteItemAction` | &Delete Line | Delete Line\|Deletes current line. |
| `DeleteItemBeginAction` | &Delete to Start of Line | Delete to Start of Line\|Deletes to start of current line. |
| `DeleteItemEndAction` | &Delete to End of Line | Delete to End of Line\|Deletes to end of current line. |
| `DeleteWordAction` | &Delete Word | Delete Word\|Deletes current word. |
| `DeleteWordBeginAction` | &Delete to Start of Word | Delete to Start of Word\|Deletes to start of current word. |
| `DeleteWordEndAction` | &Delete to End of Word | Delete to End of Word\|Deletes to end of current word. |
| `InsertItemBeforeAction` | Insert Line &Before | Insert Line Before\|Inserts new line before current one. |
| `InsertItemAfterAction` | &Insert Line After | Insert Line After\|Inserts new line after current one. |
| `SelectSectionAction` | Select Secti&on | Select Section\|Selects all lines in current section. |
| `CompareToClipboardAction` | Compare Se&lection to Clipboard | Compare Selection to Clipboard\|Compares selected text to clipboard in |
| `ConvertListAction` | Con&vert File | Convert File\|Performs picked file conversion. |
| `TrimTrailWSAction` | Trim &Trailing Whitespace | Trim Trailing Whitespace\|Strips off spaces and tab characters at the  |
| `LeadSpaceToTabAction` | &Leading Spaces to Tabs | Leading Spaces to Tabs\|Replaces spaces at the beginning of lines with |
| `TabToSpaceAction` | Tabs to &Spaces | Tabs to Spaces\|Replaces tab characters with spaces. |
| `EndingStyleListAction` | Line &Endings | Line Endings\|Converts line endings to picked style. |
| `ToWindowsAction` | To &Windows/DOS | To Windows/DOS\|Converts line endings to Windows/DOS style. |
| `ToUnixAction` | To &Unix | To Unix\|Converts line endings to Unix style. |
| `ToMacAction` | To &Macintosh | To Macintosh\|Converts line endings to Macintosh style. |
| `ConflictSectionOffNextAction` | Clear &Conflict Section, Next | Clear Conflict Section, Next\|Clears conflict for current section and  |
| `ConflictSectionNextAction` | Next &Conflict Section | Next Conflict Section\|Positions at next conflict section. |
| `ConflictSectionPrevAction` | Previous &Conflict Section | Previous Conflict Section\|Positions at previous conflict section. |
| `DiffNextAction` | Nex&t Difference | Next Difference\|Positions at next difference text. |
| `DiffPrevAction` | Previo&us Difference | Previous Difference\|Positions at previous difference text. |
| `DiffSectionNextAction` | &Next Difference Section | Next Difference Section\|Positions at next unignored difference sectio |
| `DiffSectionPrevAction` | &Previous Difference Section | Previous Difference Section\|Positions at previous unignored differenc |
| `DiffReplacedNextAction` | Next Repl&acement | Next Replacement\|Positions at next replacement text. |
| `DiffReplacedPrevAction` | Previous Replace&ment | Previous Replacement\|Positions at previous replacement text. |
| `TakenLeftNextAction` | Next Left T&aken | Next Left Taken\|Positions at next range of lines where left was taken |
| `TakenLeftPrevAction` | Previous Left T&aken | Previous Left Taken\|Positions at previous range of lines where left w |
| `TakenRightNextAction` | Next Rig&ht Taken | Next Right Taken\|Positions at next range of lines where right was tak |
| `TakenRightPrevAction` | Previous Rig&ht Taken | Previous Right Taken\|Positions at previous range of lines where right |
| `EditNextAction` | Next &Edit | Next Edit\|Positions at next edited text. |
| `EditPrevAction` | Previous E&dit | Previous Edit\|Positions at previous edited text. |
| `ReplaceAction` | &Replace... | Replace\|Replaces search string. |
| `FindInFilesAction` | Find in File&s... | Find in Files\|Finds search string in multiple files. |
| `MacFindUseSelAction` | Use Selection for Find | Use Selection for Find\|Finds selected text. |
| `GoToAction` | &Go To... | Go To\|Positions at specified line and column. |
| `BookmarkToggleListAction` | Toggle &Bookmark | Toggle Bookmark\|Sets or clears picked bookmark. |
| `BookmarkGoToListAction` | Go to Boo&kmark | Go to Bookmark\|Positions at picked bookmark. |
| `BookmarkClearAction` | C&lear Bookmarks | Clear Bookmarks\|Removes all bookmarks. |
| `GoInputAction` |  | Go Input\|Positions in input pane. |
| `GoOutputAction` |  | Go Output\|Positions in output pane. |
| `FavMergeAllAction` | Show All | Show All\|Shows unchanged, same change, left change, right change, dif |
| `FavChangedAction` | Show Changes | Show Changes\|Shows same change, left change, right change, different  |
| `FavConflictAction` | Show Conflicts | Show Conflicts\|Shows conflict lines. |
| `FavLeftAction` | Show Left Changes | Show Left Changes\|Shows same change, left change, different change an |
| `FavRightAction` | Show Right Changes | Show Right Changes\|Shows same change, right change, different change  |
| `FavMergeableAction` | Show Mergeable | Show Mergeable\|Shows same change, left change, right change and diffe |
| `FavUnchangedAction` | Show Unchanged | Show Unchanged\|Shows unchanged lines. |
| `FavMergeNoneAction` | Show None | Show None\|Shows no lines. |
| `TogNoModAction` |  | Toggle Unchanged\|Shows or hides unchanged lines. |
| `TogSameModAction` |  | Toggle Same Changes\|Shows or hides same change lines. |
| `TogLeftModAction` |  | Toggle Left Changes\|Shows or hides left change lines. |
| `TogRightModAction` |  | Toggle Right Changes\|Shows or hides right change lines. |
| `TogDiffModAction` |  | Toggle Different Changes\|Shows or hides different change lines. |
| `TogConflictAction` |  | Toggle Conflicts\|Shows or hides conflict lines. |
| `ShowContextAction` | Show &Context | Show Context\|Shows lines surrounding difference. |
| `FavorLeftAction` | Favor &Left Changes | Favor Left Changes\|Suppresses highlighting of left-only changes in ou |
| `FavorRightAction` | Fa&vor Right Changes | Favor Right Changes\|Suppresses highlighting of right-only changes in  |
| `IgnoredAction` | I&gnored | Ignored\|Ignores or unignores differences in selected lines or current |
| `ShowItemNumAction` | Line &Numbers | Line Numbers\|Shows or hides line numbers. |
| `ShowSyntaxHighlightingAction` | Syntax &Highlighting | Syntax Highlighting\|Shows or hides syntax highlighting. |
| `WordWrapAction` | Word Wra&p | Word Wrap\|Enables word wrapping in the main file view. |
| `OutputWindowAction` | Detached Out&put Pane | Detached Output Pane\|Shows output pane in separate window. |
| `ZoomAction` |  | Zoom\|Makes current pane larger. |
| `ZoomLeftAction` |  | Zoom Left\|Makes left pane incrementally larger. |
| `ZoomRightAction` |  | Zoom Right\|Makes right pane incrementally larger. |
| `WebBrowserAction` | We&bpages | Webpages\|Shows or hides webpage panels. |
| `ShowThumbnailAction` | Thu&mbnail | Thumbnail\|Shows or hides thumbnail view. |
| `ShowCenterAction` | C&enter Pane | Center Pane\|Shows or hides center pane. |
| `ShowTextDetailsAction` | Text &Details | Text Details\|Shows or hides text details panel. |
| `ShowHexDetailsAction` | He&x Details | Hex Details\|Shows or hides hexadecimal details panel. |
| `ShowAlignDetailsAction` | &Alignment Details | Alignment Details\|Shows or hides alignment details panel. |
| `ShowRulerAction` | &Ruler | Ruler\|Shows or hides ruler in details panel. |
| `OverwritingAction` |  | Overwrite\|Typing replaces characters instead of inserting them. |

### TVERACTIONS — 2 个动作

| 名称 | 标题/加速键 | 提示 |
|---|---|---|
| `IsSigAction` |  | Item Is Important\|Marks selected item as important or unimportant. |
| `ShowDetailsAction` | Text &Details | Text Details\|Shows or hides text details panel. |

## 含菜单项的表单（24 个）

### TDIRALIGNWITHITEMDIALOG — 27 个菜单项

- `FindTabItem` — Tab Character (\t) 
- `AnyItem` — Any Character (.) 
- `AlphaItem` — Any Alphanumeric Character (\w) 
- `NonAlphaItem` — Any Non-alphanumeric Character (\W) 
- `NumItem` — Any Numeric Character (\d) 
- `NonNumItem` — Any Non-numeric Character (\D) 
- `WSItem` — Any Whitespace Character (\s) 
- `CharSetItem` — Character in Set ([]) 
- `NotCharSetItem` — Character Not in Set ([^]) 
- `BeginItem` — Beginning of Line (^) 
- `EndItem` — End of Line ($) 
- `TaggedItem` — Tagged Expression (()) 
- `OrItem` — Or (|) 
- `ZeroOrMoreItem` — 0 Or More Matches (*) 
- `OneOrMoreItem` — 1 Or More Matches (+) 
- `ZeroOrOneItem` — 0 Or 1 Matches (?) 
- `ReplaceTabItem` — Tab Character (\t) 
- `FindStrItem` — Find Expression ($0) 
- `Tagged1Item` — Tagged Expression 1 ($1) 
- `Tagged2Item` — Tagged Expression 2 ($2) 
- `Tagged3Item` — Tagged Expression 3 ($3) 
- `Tagged4Item` — Tagged Expression 4 ($4) 
- `Tagged5Item` — Tagged Expression 5 ($5) 
- `Tagged6Item` — Tagged Expression 6 ($6) 
- `Tagged7Item` — Tagged Expression 7 ($7) 
- `Tagged8Item` — Tagged Expression 8 ($8) 
- `Tagged9Item` — Tagged Expression 9 ($9) 

### TDIRBASEVIEW — 4 个菜单项

- `LogClearItem` — Clear Messages 
- `LogSaveItem` — Save to File... 
- `LogCopyToClipboardItem` — Copy to Clipboard 
- `LogHideItem` — Hide Log 

### TDIRFINDDIALOG — 16 个菜单项

- `FindTabItem` — Tab Character (\t) 
- `AnyItem` — Any Character (.) 
- `AlphaItem` — Any Alphanumeric Character (\w) 
- `NonAlphaItem` — Any Non-alphanumeric Character (\W) 
- `NumItem` — Any Numeric Character (\d) 
- `NonNumItem` — Any Non-numeric Character (\D) 
- `WSItem` — Any Whitespace Character (\s) 
- `CharSetItem` — Character in Set ([]) 
- `NotCharSetItem` — Character Not in Set ([^]) 
- `BeginItem` — Beginning of Line (^) 
- `EndItem` — End of Line ($) 
- `TaggedItem` — Tagged Expression (()) 
- `OrItem` — Or (|) 
- `ZeroOrMoreItem` — 0 Or More Matches (*) 
- `OneOrMoreItem` — 1 Or More Matches (+) 
- `ZeroOrOneItem` — 0 Or 1 Matches (?) 

### TDIROTHERFILTERITEMDIALOG — 16 个菜单项

- `TabItem` — Tab Character (\t) 
- `AnyItem` — Any Character (.) 
- `AlphaItem` — Any Alphanumeric Character (\w) 
- `NonAlphaItem` — Any Non-alphanumeric Character (\W) 
- `NumItem` — Any Numeric Character (\d) 
- `NonNumItem` — Any Non-numeric Character (\D) 
- `WSItem` — Any Whitespace Character (\s) 
- `CharSetItem` — Character in Set ([]) 
- `NotCharSetItem` — Character Not in Set ([^]) 
- `BeginItem` — Beginning of Line (^) 
- `EndItem` — End of Line ($) 
- `TaggedItem` — Tagged Expression (()) 
- `OrItem` — Or (|) 
- `ZeroOrMoreItem` — 0 Or More Matches (*) 
- `OneOrMoreItem` — 1 Or More Matches (+) 
- `ZeroOrOneItem` — 0 Or 1 Matches (?) 

### TDIRSCRIPTDIALOG — 2 个菜单项

- `LogCopyItem` — Copy (16451)
- `LogSelectAllItem` — Select All (16449)

### TDIRSESSIONMISCFRAME — 3 个菜单项

- `FileFormatEditItem` — Edit... 
- `FileFormatAllItem` — Mark All 
- `FileFormatNoneItem` — Unmark All 

### TFILEFINDFRAME — 27 个菜单项

- `FindTabItem` — Tab Character (\t) 
- `AnyItem` — Any Character (.) 
- `AlphaItem` — Any Alphanumeric Character (\w) 
- `NonAlphaItem` — Any Non-alphanumeric Character (\W) 
- `NumItem` — Any Numeric Character (\d) 
- `NonNumItem` — Any Non-numeric Character (\D) 
- `WSItem` — Any Whitespace Character (\s) 
- `CharSetItem` — Character in Set ([]) 
- `NotCharSetItem` — Character Not in Set ([^]) 
- `BeginItem` — Beginning of Line (^) 
- `EndItem` — End of Line ($) 
- `TaggedItem` — Tagged Expression (()) 
- `OrItem` — Or (|) 
- `ZeroOrMoreItem` — 0 Or More Matches (*) 
- `OneOrMoreItem` — 1 Or More Matches (+) 
- `ZeroOrOneItem` — 0 Or 1 Matches (?) 
- `ReplaceTabItem` — Tab Character (\t) 
- `FindStrItem` — Find Expression ($0) 
- `Tagged1Item` — Tagged Expression 1 ($1) 
- `Tagged2Item` — Tagged Expression 2 ($2) 
- `Tagged3Item` — Tagged Expression 3 ($3) 
- `Tagged4Item` — Tagged Expression 4 ($4) 
- `Tagged5Item` — Tagged Expression 5 ($5) 
- `Tagged6Item` — Tagged Expression 6 ($6) 
- `Tagged7Item` — Tagged Expression 7 ($7) 
- `Tagged8Item` — Tagged Expression 8 ($8) 
- `Tagged9Item` — Tagged Expression 9 ($9) 

### TFILEFORMATMANAGERDIALOG — 4 个菜单项

- `MoveUpItem` — Move Up (16422)
- `MoveDownItem` — Move Down (16424)
- `DeleteItem` — Delete (46)
- `RenameItem` — Rename (113)

### THEXVIEW — 2 个菜单项

- `ThumbnailScrollItem` — Allow Scrolling 
- `ThumbnailHideItem` — Hide Thumbnail 

### THOMEVIEW — 11 个菜单项

- `SessionsOpenItem` — Open 
- `SessionsFolderOpenItem` — Open Sessions 
- `SessionsClearItem` — Clear Contents 
- `SessionsDeleteItem` — Delete (46)
- `SessionsSaveAsItem` — Save As... 
- `SessionsLockItem` — % 
- `SessionsRenameItem` — Rename (113)
- `SessionsEditItem` — Edit 
- `SessionsExpandAllItem` — Expand All 
- `SessionsCollapseAllItem` — Collapse All 
- `TaskIsFavItem` — Favorite 

### TPIXFULLSCREENDIALOG — 4 个菜单项

- `LeftItem` — Show Left (37)
- `RightItem` — Show Right (39)
- `CenterItem` — Show Difference (40)
- `ExitItem` — Exit Full Screen 

### TPROFILEBROWSEDIALOG — 5 个菜单项

- `DeleteItem` — Delete (46)
- `EditItem` — Edit 
- `RenameItem` — Rename (113)
- `ExpandAllItem` — Expand All 
- `CollapseAllItem` — Collapse All 

### TPROFILEMANAGERDIALOG — 4 个菜单项

- `DeleteItem` — Delete (46)
- `RenameItem` — Rename (113)
- `ExpandAllItem` — Expand All 
- `CollapseAllItem` — Collapse All 

### TPROFILESAVEASDIALOG — 3 个菜单项

- `NewSubfolderItem` — New Subfolder (45)
- `DeleteItem` — Delete (46)
- `RenameItem` — Rename (113)

### TPROGOPTIONSDIALOG — 2 个菜单项

- `CommandMenuAllowedAllItem` — Show All in Menu 
- `CommandToolbarAllowedAllItem` — Show All on Toolbar 

### TSESSIONSAVEASDIALOG — 3 个菜单项

- `NewSubfolderItem` — New Subfolder (45)
- `DeleteItem` — Delete (46)
- `RenameItem` — Rename (113)

### TTABLEVIEW — 2 个菜单项

- `ThumbnailScrollItem` — Allow Scrolling 
- `ThumbnailHideItem` — Hide Thumbnail 

### TTEXTFINDINFILESDIALOG — 16 个菜单项

- `TabItem` — Tab Character (\t) 
- `AnyItem` — Any Character (.) 
- `AlphaItem` — Any Alphanumeric Character (\w) 
- `NonAlphaItem` — Any Non-alphanumeric Character (\W) 
- `NumItem` — Any Numeric Character (\d) 
- `NonNumItem` — Any Non-numeric Character (\D) 
- `WSItem` — Any Whitespace Character (\s) 
- `CharSetItem` — Character in Set ([]) 
- `NotCharSetItem` — Character Not in Set ([^]) 
- `BeginItem` — Beginning of Line (^) 
- `EndItem` — End of Line ($) 
- `TaggedItem` — Tagged Expression (()) 
- `OrItem` — Or (|) 
- `ZeroOrMoreItem` — 0 Or More Matches (*) 
- `OneOrMoreItem` — 1 Or More Matches (+) 
- `ZeroOrOneItem` — 0 Or 1 Matches (?) 

### TTEXTGRAMMARITEMDIALOG — 16 个菜单项

- `TabItem` — Tab Character (\t) 
- `AnyItem` — Any Character (.) 
- `AlphaItem` — Any Alphanumeric Character (\w) 
- `NonAlphaItem` — Any Non-alphanumeric Character (\W) 
- `NumItem` — Any Numeric Character (\d) 
- `NonNumItem` — Any Non-numeric Character (\D) 
- `WSItem` — Any Whitespace Character (\s) 
- `CharSetItem` — Character in Set ([]) 
- `NotCharSetItem` — Character Not in Set ([^]) 
- `BeginItem` — Beginning of Line (^) 
- `EndItem` — End of Line ($) 
- `FormFeedItem` — Form Feed Character (\xc) 
- `OrItem` — Or (|) 
- `ZeroOrMoreItem` — 0 Or More Matches (*) 
- `OneOrMoreItem` — 1 Or More Matches (+) 
- `ZeroOrOneItem` — 0 Or 1 Matches (?) 

### TTEXTINSIGITEMDIALOG — 16 个菜单项

- `TabItem` — Tab Character (\t) 
- `AnyItem` — Any Character (.) 
- `AlphaItem` — Any Alphanumeric Character (\w) 
- `NonAlphaItem` — Any Non-alphanumeric Character (\W) 
- `NumItem` — Any Numeric Character (\d) 
- `NonNumItem` — Any Non-numeric Character (\D) 
- `WSItem` — Any Whitespace Character (\s) 
- `CharSetItem` — Character in Set ([]) 
- `NotCharSetItem` — Character Not in Set ([^]) 
- `BeginItem` — Beginning of Line (^) 
- `EndItem` — End of Line ($) 
- `TaggedItem` — Tagged Expression (()) 
- `OrItem` — Or (|) 
- `ZeroOrMoreItem` — 0 Or More Matches (*) 
- `OneOrMoreItem` — 1 Or More Matches (+) 
- `ZeroOrOneItem` — 0 Or 1 Matches (?) 

### TTEXTREPLACEMENTITEMDIALOG — 27 个菜单项

- `FindTabItem` — Tab Character (\t) 
- `AnyItem` — Any Character (.) 
- `AlphaItem` — Any Alphanumeric Character (\w) 
- `NonAlphaItem` — Any Non-alphanumeric Character (\W) 
- `NumItem` — Any Numeric Character (\d) 
- `NonNumItem` — Any Non-numeric Character (\D) 
- `WSItem` — Any Whitespace Character (\s) 
- `CharSetItem` — Character in Set ([]) 
- `NotCharSetItem` — Character Not in Set ([^]) 
- `BeginItem` — Beginning of Line (^) 
- `EndItem` — End of Line ($) 
- `TaggedItem` — Tagged Expression (()) 
- `OrItem` — Or (|) 
- `ZeroOrMoreItem` — 0 Or More Matches (*) 
- `OneOrMoreItem` — 1 Or More Matches (+) 
- `ZeroOrOneItem` — 0 Or 1 Matches (?) 
- `ReplaceTabItem` — Tab Character (\t) 
- `FindStrItem` — Find Expression ($0) 
- `Tagged1Item` — Tagged Expression 1 ($1) 
- `Tagged2Item` — Tagged Expression 2 ($2) 
- `Tagged3Item` — Tagged Expression 3 ($3) 
- `Tagged4Item` — Tagged Expression 4 ($4) 
- `Tagged5Item` — Tagged Expression 5 ($5) 
- `Tagged6Item` — Tagged Expression 6 ($6) 
- `Tagged7Item` — Tagged Expression 7 ($7) 
- `Tagged8Item` — Tagged Expression 8 ($8) 
- `Tagged9Item` — Tagged Expression 9 ($9) 

### TTEXTVIEW — 5 个菜单项

- `GapCollapseItem` — Collapse Filtered Gap 
- `GapExpandItem` — Expand Filtered Gap 
- `GapShowBarsItem` — Show Filtered Line Counts 
- `ThumbnailScrollItem` — Allow Scrolling 
- `ThumbnailHideItem` — Hide Thumbnail 

### TTEXTWEIGHTITEMDIALOG — 16 个菜单项

- `TabItem` — Tab Character (\t) 
- `AnyItem` — Any Character (.) 
- `AlphaItem` — Any Alphanumeric Character (\w) 
- `NonAlphaItem` — Any Non-alphanumeric Character (\W) 
- `NumItem` — Any Numeric Character (\d) 
- `NonNumItem` — Any Non-numeric Character (\D) 
- `WSItem` — Any Whitespace Character (\s) 
- `CharSetItem` — Character in Set ([]) 
- `NotCharSetItem` — Character Not in Set ([^]) 
- `BeginItem` — Beginning of Line (^) 
- `EndItem` — End of Line ($) 
- `TaggedItem` — Tagged Expression (()) 
- `OrItem` — Or (|) 
- `ZeroOrMoreItem` — 0 Or More Matches (*) 
- `OneOrMoreItem` — 1 Or More Matches (+) 
- `ZeroOrOneItem` — 0 Or 1 Matches (?) 

### TWORKSPACEMANAGERDIALOG — 2 个菜单项

- `DeleteItem` — Delete (46)
- `RenameItem` — Rename (113)
