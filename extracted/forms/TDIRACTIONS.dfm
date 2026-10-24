object DirActions: TDirActions
  object List: TUiActionList
    object ExpandAction: TUiAction
      Category = 'Disjoint'
    end
    object CollapseAction: TUiAction
      Category = 'Disjoint'
    end
    object ExpandSubfoldersAction: TUiAction
      Category = 'Disjoint'
    end
    object CollapseSubfoldersAction: TUiAction
      Category = 'Disjoint'
    end
    object NameFilterEditAction: TUiAction
      Category = 'Session'
      Hint = 'Name Filters Edit|Focuses on edit listing current name file filters.'
      ShortCaption = 'Filters:'
    end
    object NameFilterAction: TUiAction
      Category = 'Session'
      Hint = 'Name Filters|Edits name file filters.'
      ImageIndex = imgFilters
      ShortCaption = 'Filters'
    end
    object SpecsBackAction: TUiAction
      Category = 'Session'
      Caption = 'Back'
      Hint = 'Back|Changes to previous base folders.'
      ImageIndex = imgSpecsBack
      MacShortCutStr = 'Meta+['
      ShortCutStr = 'Alt+Left'
    end
    object SpecsForwardAction: TUiAction
      Category = 'Session'
      Caption = 'Forward'
      Hint = 'Forward|Changes to next base folders.'
      ImageIndex = imgSpecsForward
      MacShortCutStr = 'Meta+]'
      ShortCutStr = 'Alt+Right'
    end
    object UpOneLevelListAction: TUiAction
      Category = 'Session'
      Caption = 'Up One Level'
      Hint = 'Up One Level|Changes base folders on picked sides to their parent folders.'
      ImageIndex = imgUpOneLevel
    end
    object UpOneLevelLeftAction: TUiAction
      Category = 'Session'
      Caption = '&Left Side'
      Hint = 'Up One Level on Left Side|Changes left base folder to its parent folder.'
    end
    object UpOneLevelCenterAction: TUiAction
      Category = 'Session'
      Caption = '&Center Side'
      Hint = 'Up One Level on Center Side|Changes center base folder to its parent folder.'
    end
    object UpOneLevelRightAction: TUiAction
      Category = 'Session'
      Caption = '&Right Side'
      Hint = 'Up One Level on Right Side|Changes right base folder to its parent folder.'
    end
    object UpOneLevelOutputAction: TUiAction
      Category = 'Session'
      Caption = '&Output Side'
      Hint = 'Up One Level on Output Side|Changes output base folder to its parent folder.'
    end
    object UpOneLevelAllAction: TUiAction
      Category = 'Session'
      MacShortCutStr = 'Meta+Up'
    end
    object MergeBaseViewAction: TUiAction
      Category = 'Session'
      Caption = '&Merge Base Folders'
      Hint = 'Merge Base Folders|Merges base folders in new view.'
      ImageIndex = imgDirMergeSession
      ShortCaption = 'Merge View'
      ToolbarAllowed = False
    end
    object SyncBaseViewAction: TUiAction
      Category = 'Session'
      Caption = 'S&ync Base Folders'
      Hint = 'Sync Base Folders|Synchronizes base folders in new view.'
      ImageIndex = imgDirSyncSession
      ShortCaption = 'Sync View'
      ToolbarAllowed = False
    end
    object CompareToOutputListAction: TUiAction
      Category = 'Session'
      Caption = 'Compare to O&utput'
      Hint = 'Compare to Output|Compares picked side and output in new view.'
    end
    object CompareLeftToOutputAction: TUiAction
      Category = 'Session'
      Caption = '&Left Side'
      Hint = 'Compare Left to Output|Compares left and output in new view.'
    end
    object CompareCenterToOutputAction: TUiAction
      Category = 'Session'
      Caption = '&Center Side'
      Hint = 'Compare Center to Output|Compares center and output in new view.'
    end
    object CompareRightToOutputAction: TUiAction
      Category = 'Session'
      Caption = '&Right Side'
      Hint = 'Compare Right to Output|Compares right and output in new view.'
    end
    object QuickCompareAction: TUiAction
      Category = 'Actions'
      Caption = '&Quick Compare'
      Hint = 'Quick Compare|Quick compare selected files.'
    end
    object CompareToAction: TUiAction
      Category = 'Actions'
      Caption = 'Compare To...'
      Hint = 'Compare To|Marks item for comparing in new view.'
      ShortCutStr = 'F7'
    end
    object AlignWithAction: TUiAction
      Category = 'Actions'
      Hint = 'Align With|Marks item for manual realignment.'
      ShortCutStr = 'F6'
    end
    object CompareAction: TUiAction
      Category = 'Actions'
      Caption = '&Compare Contents'
      Hint = 'Compare Contents|Determines overall comparison state for selected items.'
      ImageIndex = imgCompare
      ShortCaption = 'Compare'
      ToolbarAllowed = False
    end
    object MergeAction: TUiAction
      Category = 'Actions'
      Caption = '&Merge...'
      Hint = 'Merge|Performs automated merge of selected items.'
      ShortCaption = 'Merge'
    end
    object CopyRightAction: TUiAction
      Category = 'Actions'
      Caption = 'Cop&y to Right'
      Hint = 'Copy to Right|Copies selected items from left to right.'
      ImageIndex = imgCopyRight
      MacShortCutStr = 'Alt+Meta+Right'
      MenuAllowed = False
      ShortCaption = 'Copy'
      ShortCutStr = 'Ctrl+R'
      ToolbarAllowed = False
    end
    object CopyLeftAction: TUiAction
      Category = 'Actions'
      Caption = 'Cop&y to Left'
      Hint = 'Copy to Left|Copies selected items from right to left.'
      ImageIndex = imgCopyLeft
      MacShortCutStr = 'Alt+Meta+Left'
      MenuAllowed = False
      ShortCaption = 'Copy'
      ShortCutStr = 'Ctrl+L'
      ToolbarAllowed = False
    end
    object CopyPromptAction: TUiAction
      Category = 'Actions'
      Caption = 'Cop&y to Side...'
      Hint = 'Copy to Side|Prompts which side to copy selected items to.'
      ImageIndex = imgCopyLeftOrRight
      MenuAllowed = False
      ShortCaption = 'Copy'
      ToolbarAllowed = False
    end
    object CopySideAction: TUiAction
      Category = 'Actions'
      Hint = 'Copy to Other Side|Copies selected items to other side.'
    end
    object CopyToOutputAction: TUiAction
      Category = 'Actions'
      Caption = 'Cop&y to Output...'
      Hint = 'Copy to Output|Copies selected items to output folder.'
      ImageIndex = imgCopyToOutput
      ShortCaption = 'To Output'
    end
    object MoveRightAction: TUiAction
      Category = 'Actions'
      Caption = '&Move to Right'
      Hint = 'Move to Right|Moves selected items from left to right.'
      ImageIndex = imgMoveRight
      MenuAllowed = False
      ShortCaption = 'Move'
      ToolbarAllowed = False
    end
    object MoveLeftAction: TUiAction
      Category = 'Actions'
      Caption = '&Move to Left'
      Hint = 'Move to Left|Moves selected items from right to left.'
      ImageIndex = imgMoveLeft
      MenuAllowed = False
      ShortCaption = 'Move'
      ToolbarAllowed = False
    end
    object MovePromptAction: TUiAction
      Category = 'Actions'
      Caption = '&Move to Side...'
      Hint = 'Move to Side|Prompts which side to move selected items to.'
      ImageIndex = imgMoveLeftOrRight
      MenuAllowed = False
      ShortCaption = 'Move'
      ToolbarAllowed = False
    end
    object MoveSideAction: TUiAction
      Category = 'Actions'
      Hint = 'Move to Other Side|Moves selected items to other side.'
      ToolbarAllowed = False
    end
    object MoveBothAction: TUiAction
      Category = 'Actions'
      Caption = 'Exchange'
      Hint = 'Exchange|Moves selected items to other side.'
      ImageIndex = imgMoveBoth
      MenuAllowed = False
      ShortCaption = 'Exchange'
      ToolbarAllowed = False
    end
    object CopyToAction: TUiAction
      Category = 'Actions'
      Caption = 'Copy to &Folder...'
      Hint = 'Copy to Folder|Copies selected items to another folder.'
      ImageIndex = imgCopyTo
      ShortCaption = 'Copy To'
      ToolbarAllowed = False
    end
    object MoveToAction: TUiAction
      Category = 'Actions'
      Caption = 'Mo&ve to Folder...'
      Hint = 'Move to Folder|Moves selected items to another folder.'
      ImageIndex = imgMoveTo
      ShortCaption = 'Move To'
      ToolbarAllowed = False
    end
    object DeleteAction: TUiAction
      Category = 'Actions'
      Caption = '&Delete'
      Hint = 'Delete|Deletes selected items.'
      ImageIndex = imgDelete
      MacShortCutStr = 'Meta+BkSp'
      ShortCaption = 'Delete'
      ToolbarAllowed = False
    end
    object PermanentDeleteAction: TUiAction
      Category = 'Actions'
      Hint = 'Delete Permanently|Deletes selected items without moving them to the recycle bin.'
      MacShortCutStr = 'Meta+Alt+BkSp'
      ShortCutStr = 'Shift+Del'
    end
    object RenameAction: TUiAction
      Category = 'Actions'
      Caption = '&Rename'
      Hint = 'Rename|Renames selected items.'
      ImageIndex = imgRename
      MacShortCutStr = 'Alt+Enter'
      ShortCaption = 'Rename'
      ShortCutStr = 'F2'
      ToolbarAllowed = False
    end
    object AttributesAction: TUiAction
      Category = 'Actions'
      Caption = '&Attributes...'
      Hint = 'Attributes|Sets the DOS attributes of selected files.'
    end
    object TouchAction: TUiAction
      Category = 'Actions'
      Caption = '&Touch...'
      Hint = 'Touch|Sets timestamps of selected items.'
      ImageIndex = imgTouch
      ShortCaption = 'Touch'
      ToolbarAllowed = False
    end
    object NewFolderAction: TUiAction
      Category = 'Actions'
      Caption = '&New Folder...'
      Hint = 'New Folder|Creates a new folder.'
      ImageIndex = imgNewFolder
      MacShortCutStr = 'Shift+Meta+N'
      ShortCaption = 'Folder'
      ShortCutStr = 'Ins'
      ToolbarAllowed = False
    end
    object IgnoredAction: TUiAction
      Category = 'Actions'
      Caption = 'I&gnored'
      Hint = 'Ignored|Ignores or unignores differences in selected items.'
      ImageIndex = imgIgnored
      ShortCaption = 'Ignored'
      ToolbarAllowed = False
    end
    object FileReportAction: TUiAction
      Category = 'Actions'
      Caption = 'File Compare Re&port...'
      Hint = 'File Compare Report|Produces file comparison report.'
      ImageIndex = imgReport
      MacShortCutStr = 'Alt+Meta+P'
      ShortCaption = 'File Report'
      ToolbarAllowed = False
    end
    object SyncListAction: TUiAction
      Category = 'Actions'
      Caption = 'Synchroni&ze'
      Hint = 'Synchronize|Synchronizes by picked method.'
    end
    object UpdateRightAction: TUiAction
      Category = 'Actions'
      Caption = 'Update &Right...'
      Hint = 'Update Right|Synchronizes by copying newer and orphan items from left to right.'
      ImageIndex = imgUpdateRight
      ShortCaption = 'Update Right'
      ToolbarAllowed = False
    end
    object UpdateLeftAction: TUiAction
      Category = 'Actions'
      Caption = 'Update &Left...'
      Hint = 'Update Left|Synchronizes by copying newer and orphan items from right to left.'
      ImageIndex = imgUpdateLeft
      ShortCaption = 'Update Left'
      ToolbarAllowed = False
    end
    object UpdateBothAction: TUiAction
      Category = 'Actions'
      Caption = 'Update &Both...'
      Hint = 'Update Both|Synchronizes by copying newer and orphan items from left to right and from right to left.'
      ImageIndex = imgUpdateBoth
      ShortCaption = 'Update Both'
      ToolbarAllowed = False
    end
    object MirrorRightAction: TUiAction
      Category = 'Actions'
      Caption = 'Mirror to Ri&ght...'
      Hint = 'Mirror to Right|Synchronizes by replacing all different items on right, deleting any orphan items on right, and copying any left orphan items to right.'
      ImageIndex = imgMirrorRight
      MacShortCutStr = 'Ctrl+Meta+Right'
      ShortCaption = 'Mirror Right'
      ShortCutStr = 'Shift+Ctrl+R'
      ToolbarAllowed = False
    end
    object MirrorLeftAction: TUiAction
      Category = 'Actions'
      Caption = 'Mirror to Le&ft...'
      Hint = 'Mirror to Left|Synchronizes by replacing all different items on left, deleting any orphan items on left, and copying any right orphan items to left.'
      ImageIndex = imgMirrorLeft
      MacShortCutStr = 'Ctrl+Meta+Left'
      ShortCaption = 'Mirror Left'
      ShortCutStr = 'Shift+Ctrl+L'
      ToolbarAllowed = False
    end
    object SourceControlListAction: TUiAction
      Category = 'Actions'
      Caption = 'So&urce Control'
      Hint = 'Source Control|Performs picked source control command.'
    end
    object VcsAddAction: TUiAction
      Category = 'Actions'
      Caption = '&Add to Source Control'
      Hint = 'Add to Source Control|Adds selected items to source control.'
    end
    object VcsRemoveAction: TUiAction
      Category = 'Actions'
      Caption = '&Remove from Source Control'
      Hint = 'Remove from Source Control|Removes selected items from source control.'
    end
    object VcsGetLatestAction: TUiAction
      Category = 'Actions'
      Caption = 'Get Latest &Version'
      Hint = 'Get Latest Version|Gets latest version of items from source control.'
    end
    object VcsGetAction: TUiAction
      Category = 'Actions'
      Caption = '&Get...'
      Hint = 'Get|Gets particular version of items from source control.'
      MenuAllowed = False
    end
    object VcsCheckInAction: TUiAction
      Category = 'Actions'
      Caption = 'Check &In...'
      Hint = 'Check In|Checks item into source control.'
    end
    object VcsCheckOutAction: TUiAction
      Category = 'Actions'
      Caption = 'Check &Out'
      Hint = 'Check Out|Checks out item from source control.'
    end
    object VcsUndoCheckOutAction: TUiAction
      Category = 'Actions'
      Caption = '&Undo Check Out'
      Hint = 'Undo Check Out|Undoes checkout from source control.'
    end
    object VcsDiffAction: TUiAction
      Category = 'Actions'
      Caption = 'Show &Differences'
      Hint = 'Show Differences|Shows source control differences.'
    end
    object VcsHistoryAction: TUiAction
      Category = 'Actions'
      Caption = 'Show &History'
      Hint = 'Show History|Shows source control history.'
    end
    object VcsPropertiesAction: TUiAction
      Category = 'Actions'
      Caption = 'Show &Properties'
      Hint = 'Show Properties|Shows source control properties.'
    end
    object VcsRunAppAction: TUiAction
      Category = 'Actions'
      Caption = 'Ru&n Source Control Application'
      Hint = 'Run Source Control Application|Runs source control application.'
    end
    object SelectAllFilesAction: TUiAction
      Category = 'Edit'
      Caption = 'Select All &Files'
      Hint = 'Select All Files|Selects all visible files.'
      ImageIndex = imgSelectAllFiles
      MacShortCutStr = 'Shift+Meta+A'
      ShortCaption = 'Files'
      ShortCutStr = 'Shift+Ctrl+A'
    end
    object SelectNewerListAction: TUiAction
      Category = 'Edit'
      Caption = 'Select &Newer'
      Hint = 'Select Newer|Selects all newer files on picked sides.'
    end
    object SelectNewerLeftAction: TUiAction
      Category = 'Edit'
      Caption = '&Left Side'
      Hint = 'Select Left Newer|Selects all newer files on the left.'
    end
    object SelectNewerRightAction: TUiAction
      Category = 'Edit'
      Caption = '&Right Side'
      Hint = 'Select Right Newer|Selects all newer files on the right.'
    end
    object SelectNewerBothAction: TUiAction
      Category = 'Edit'
      Caption = '&Both Sides'
      Hint = 'Select Both Newer|Selects all newer files on both sides.'
    end
    object SelectOrphanListAction: TUiAction
      Category = 'Edit'
      Caption = 'Select &Orphans'
      Hint = 'Select Orphans|Selects all orphan files on picked sides.'
    end
    object SelectOrphanLeftAction: TUiAction
      Category = 'Edit'
      Caption = '&Left Side'
      Hint = 'Select Left Orphans|Selects all orphan files on the left.'
    end
    object SelectOrphanRightAction: TUiAction
      Category = 'Edit'
      Caption = '&Right Side'
      Hint = 'Select Right Orphans|Selects all orphan files on the right.'
    end
    object SelectOrphanBothAction: TUiAction
      Category = 'Edit'
      Caption = '&Both Sides'
      Hint = 'Select Both Orphans|Selects all orphan files on both sides.'
    end
    object DiffNextAction: TUiAction
      Category = 'Search'
      Caption = '&Next Difference'
      Hint = 'Next Difference|Positions at next difference.'
      ImageIndex = imgDown
      MacShortCutStr = 'Ctrl+Alt+Down'
      ShortCaption = 'Next Diff'
      ShortCutStr = 'Ctrl+N'
      ToolbarAllowed = False
    end
    object DiffPrevAction: TUiAction
      Category = 'Search'
      Caption = '&Previous Difference'
      Hint = 'Previous Difference|Positions at previous difference.'
      ImageIndex = imgUp
      MacShortCutStr = 'Ctrl+Alt+Up'
      ShortCaption = 'Prev Diff'
      ShortCutStr = 'Ctrl+P'
      ToolbarAllowed = False
    end
    object FavCompareAllAction: TUiAction
      Category = 'Favorites'
      Caption = 'Show All'
      Hint = 'Show All|Shows same, left orphan, right orphan, left newer, right newer and difference items.'
      ImageIndex = imgFavAll
      MacShortCutStr = 'Meta+1'
      ShortCaption = 'All'
    end
    object FavDiffAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Differences'
      Hint = 'Show Differences|Shows left orphan, right orphan, left newer, right newer and difference items.'
      ImageIndex = imgFavDiff
      MacShortCutStr = 'Meta+2'
      ShortCaption = 'Diffs'
    end
    object FavSameAction: TUiAction
      Category = 'Favorites'
      Caption = 'Show Same'
      Hint = 'Show Same|Shows same items.'
      ImageIndex = imgFavSame
      MacShortCutStr = 'Meta+3'
      ShortCaption = 'Same'
    end
    object FavNoOrphanAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show No Orphans'
      Hint = 'Show No Orphans|Shows same, left newer, right newer and difference items.'
      ShortCaption = 'No Orphans'
    end
    object FavDiffNoOrphanAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Differences but No Orphans'
      Hint = 'Show Differences but No Orphans|Shows left newer, right newer and difference items.'
      ShortCaption = 'Diffs No Orphans'
    end
    object FavOrphanAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Orphans'
      Hint = 'Show Orphans|Shows left orphan and right orphan items.'
      ShortCaption = 'Orphans'
    end
    object FavLeftNewerAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Left Newer'
      Hint = 'Show Left Newer|Shows left newer items.'
      ShortCaption = 'Left Newer'
    end
    object FavRightNewerAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Right Newer'
      Hint = 'Show Right Newer|Shows right newer items.'
      ShortCaption = 'Right Newer'
    end
    object FavLeftNewerOrphanAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Left Newer and Left Orphans'
      Hint = 'Show Left Newer and Left Orphans|Shows left orphan and left newer items.'
      ShortCaption = 'Left Newer, Orphans'
    end
    object FavRightNewerOrphanAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Right Newer and Right Orphans'
      Hint = 'Show Right Newer and Right Orphans|Shows right orphan and right newer items.'
      ShortCaption = 'Right Newer, Orphans'
    end
    object FavLeftOrphanAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Left Orphans'
      Hint = 'Show Left Orphans|Shows left orphan items.'
      ShortCaption = 'Left Orphans'
    end
    object FavRightOrphanAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Right Orphans'
      Hint = 'Show Right Orphans|Shows right orphan items.'
      ShortCaption = 'Right Orphans'
    end
    object FavCompareNoneAction: TUiAction
      Category = 'View'
      Caption = 'Show None'
      Hint = 'Show None|Hides all files.'
      ImageIndex = imgFavNone
      MenuAllowed = False
      ShortCaption = 'None'
      ToolbarAllowed = False
    end
    object FavMergeAllAction: TUiAction
      Category = 'Favorites'
      Caption = 'Show All'
      Hint = 'Show All|Shows unchanged, same change, left add, right add, left delete, right delete, left change, right change, difference change and conflict items.'
      ImageIndex = imgFavAll
      MacShortCutStr = 'Meta+1'
      ShortCaption = 'All'
    end
    object FavChangedAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Changes'
      Hint = 'Show Changes|Shows left add, right add, left delete, right delete, left change, right change and conflict items.'
      ImageIndex = imgFavDiff
      MacShortCutStr = 'Meta+2'
      ShortCaption = 'Diffs'
    end
    object FavConflictAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Conflicts'
      Hint = 'Show Conflicts|Shows conflict items.'
      MacShortCutStr = 'Meta+3'
      ShortCaption = 'Conflicts'
    end
    object FavLeftAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Left Changes'
      Hint = 'Show Left Changes|Shows left add, left delete and left change items.'
      MacShortCutStr = 'Meta+4'
      ShortCaption = 'Left'
    end
    object FavRightAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Right Changes'
      Hint = 'Show Right Changes|Shows right add, right delete and right change items.'
      MacShortCutStr = 'Meta+5'
      ShortCaption = 'Right'
    end
    object FavMergeableAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Mergeable'
      Hint = 'Show Mergeable|Shows same change and difference change items.'
      MacShortCutStr = 'Meta+6'
      ShortCaption = 'Okay'
    end
    object FavUnchangedAction: TUiAction
      Category = 'Favorites'
      Caption = 'Show Unchanged'
      Hint = 'Show Unchanged|Shows unchanged items.'
      ImageIndex = imgFavSame
      MacShortCutStr = 'Meta+7'
      ShortCaption = 'Same'
    end
    object FavMergeNoneAction: TUiAction
      Category = 'View'
      Caption = 'Show None'
      Hint = 'Show None|Shows no items.'
      ImageIndex = imgFavNone
      MacShortCutStr = 'Meta+8'
      MenuAllowed = False
      ShortCaption = 'None'
      ToolbarAllowed = False
    end
    object TogSameAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Same|Shows or hides same items.'
      ShortCaption = 'Same'
    end
    object TogLeftOrphanAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Left Orphans|Shows or hides left orphan items.'
      ShortCaption = 'Left Orphans'
    end
    object TogRightOrphanAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Right Orphans|Shows or hides right orphan items.'
      ShortCaption = 'Right Orphans'
    end
    object TogLeftNewerAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Left Newer|Shows or hides left newer items.'
      ShortCaption = 'Left Newer'
    end
    object TogRightNewerAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Right Newer|Shows or hides right newer items.'
      ShortCaption = 'Right Newer'
    end
    object TogDiffAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Differences|Shows or hides difference items.'
      ShortCaption = 'Diffs'
    end
    object TogNoModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Unchanged|Shows or hides unchanged items.'
      ShortCaption = 'Same'
    end
    object TogSameModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Same Changes|Shows or hides same change items.'
      ShortCaption = 'Same Diffs'
    end
    object TogLeftAddAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Left Adds|Shows or hides left add items.'
      ShortCaption = 'Left Adds'
    end
    object TogRightAddAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Right Adds|Shows or hides right add items.'
      ShortCaption = 'Right Adds'
    end
    object TogLeftDelAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Left Deletes|Shows or hides left delete items.'
      ShortCaption = 'Left Dels'
    end
    object TogRightDelAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Right Deletes|Shows or hides right delete items.'
      ShortCaption = 'Right Dels'
    end
    object TogLeftModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Left Changes|Shows or hides left change items.'
      ShortCaption = 'Left Mods'
    end
    object TogRightModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Right Changes|Shows or hides right change items.'
      ShortCaption = 'Right Mods'
    end
    object TogDiffModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Mergeable|Shows or hides mergeable items.'
      ShortCaption = 'Diffs'
    end
    object TogConflictAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Conflicts|Shows or hides conflict items.'
      ShortCaption = 'Conflicts'
    end
    object DirShowAllAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Always Show Folders'
      GroupIndex = 10
      Hint = 'Always Show Folders|Shows all folders, ignoring the display filter.'
      ImageIndex = imgDirShowAll
      ShortCaption = 'All'
    end
    object DirCompareStructureAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Compare Files and Fol&der Structure'
      GroupIndex = 10
      Hint = 'Compare Files and Folder Structure|Shows folders if they, or items they contain, match the display filter.'
      ImageIndex = imgDirCompareStructure
      ShortCaption = 'Structure'
    end
    object DirCompareFilesOnlyAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Only Compare &Files'
      GroupIndex = 10
      Hint = 'Only Compare Files|Shows folders only if they contain files matching the display filter.'
      ImageIndex = imgDirCompareFilesOnly
      ShortCaption = 'Files'
    end
    object DirFlattenAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Ignore Folder Structure'
      GroupIndex = 10
      Hint = 'Ignore Folder Structure (Flatten)|Compares all files as if they were in a single folder.'
      ImageIndex = imgDirFlatten
      ShortCaption = 'Flatten'
    end
    object ShowCenterAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Ce&nter Pane'
      Hint = 'Center Pane|Shows or hides center pane.'
      ImageIndex = imgShowCenter
      ShortCaption = 'Center'
      ToolbarAllowed = False
    end
  end
  object Tree: TUiActionTree
    Nodes = ('Session: Menu', ('Swap: MenuItem', 'SpecsBack: MenuItem', 'SpecsForward: MenuItem', 'BrowseList: SubmenuItem', (), 'UpOneLevelList: SubmenuItem', ('UpOneLevelLeft: MenuItem', 'UpOneLevelCenter: MenuItem', 'UpOneLevelRight: MenuItem', 'UpOneLevelOutput: MenuItem', 'UpOneLevelAll: MenuItem'), 'Views: SeparatorItem', 'MergeBaseView: MenuItem', 'SyncBaseView: MenuItem', 'CompareToOutputList: SubmenuItem', ('CompareLeftToOutput: MenuItem', 'CompareCenterToOutput: MenuItem', 'CompareRightToOutput: MenuItem')), 'Actions: Menu', ('OpenWithList: SubmenuItem', (), 'QuickCompare: MenuItem', 'CompareTo: MenuItem', 'AlignWith: MenuItem', 'Common: SeparatorItem', 'Compare: MenuItem', 'Merge: MenuItem', 'CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopyPrompt: MenuItem', 'CopySide: MenuItem', 'CopyToOutput: MenuItem', 'MoveRight: MenuItem', 'MoveLeft: MenuItem', 'MovePrompt: MenuItem', 'MoveSide: MenuItem', 'MoveBoth: MenuItem', 'CopyTo: MenuItem', 'MoveTo: MenuItem', 'Delete: MenuItem', 'Rename: MenuItem', 'Attributes: MenuItem', 'Touch: MenuItem', 'Exclude: MenuItem', 'NewFolder: MenuItem', 'CopyFilenames: MenuItem', 'Ignored: MenuItem', 'RefreshSelection: MenuItem', 'FileReport: MenuItem', 'Sync: SeparatorItem', 'SyncList: SubmenuItem', ('UpdateRight: MenuItem', 'UpdateLeft: MenuItem', 'UpdateBoth: MenuItem', 'MirrorRight: MenuItem', 'MirrorLeft: MenuItem'), 'Last: SeparatorItem', 'SourceControlList: SubmenuItem', ('VcsAdd: MenuItem', 'VcsRemove: MenuItem', 'VcsGetLatest: MenuItem', 'VcsGet: MenuItem', 'N1: SeparatorItem', 'VcsCheckIn: MenuItem', 'VcsCheckOut: MenuItem', 'VcsUndoCheckOut: MenuItem', 'N2: SeparatorItem', 'VcsDiff: MenuItem', 'VcsHistory: MenuItem', 'VcsProperties: MenuItem', 'N3: SeparatorItem', 'VcsRunApp: MenuItem')), 'Edit: Menu', ('SelectAll: MenuItem', 'SelectAllFiles: MenuItem', 'SelectNewerList: SubmenuItem', ('SelectNewerLeft: MenuItem', 'SelectNewerRight: MenuItem', 'SelectNewerBoth: MenuItem'), 'SelectOrphanList: SubmenuItem', ('SelectOrphanLeft: MenuItem', 'SelectOrphanRight: MenuItem', 'SelectOrphanBoth: MenuItem')), 'Search: Menu', ('DiffNext: MenuItem', 'DiffPrev: MenuItem'), 'View: Menu', ('FavCompareAll: MenuItem', 'FavDiff: MenuItem', 'FavSame: MenuItem', 'FavNoOrphan: MenuItem', 'FavDiffNoOrphan: MenuItem', 'FavOrphan: MenuItem', 'FavLeftNewer: MenuItem', 'FavRightNewer: MenuItem', 'FavLeftNewerOrphan: MenuItem', 'FavRightNewerOrphan: MenuItem', 'FavLeftOrphan: MenuItem', 'FavRightOrphan: MenuItem', 'FavCompareNone: MenuItem', 'FavMergeAll: MenuItem', 'FavChanged: MenuItem', 'FavConflict: MenuItem', 'FavLeft: MenuItem', 'FavRight: MenuItem', 'FavMergeable: MenuItem', 'FavUnchanged: MenuItem', 'FavMergeNone: MenuItem', 'DirHandling: SeparatorItem', 'DirShowAll: MenuItem', 'DirCompareStructure: MenuItem', 'DirCompareFilesOnly: MenuItem', 'DirFlatten: MenuItem', 'InsigIgnored: SeparatorItem', 'Layout: SeparatorItem', 'ShowCenter: MenuItem'), 'Main: Toolbar', ('SessionLocked: ToolButton', 'DisplayFilters: SeparatorButton', 'FavCompareAll: ToolButton', 'FavMergeAll: ToolButton', 'DisplayFilters: SubmenuButton', ('FavDiff: MenuItem', 'FavNoOrphan: MenuItem', 'FavDiffNoOrphan: MenuItem', 'FavOrphan: MenuItem', 'FavLeftNewer: MenuItem', 'FavRightNewer: MenuItem', 'FavLeftNewerOrphan: MenuItem', 'FavRightNewerOrphan: MenuItem', 'FavLeftOrphan: MenuItem', 'FavRightOrphan: MenuItem', 'FavChanged: MenuItem', 'FavConflict: MenuItem', 'FavLeft: MenuItem', 'FavRight: MenuItem', 'FavMergeable: MenuItem'), 'FavDiff: ToolButton', 'FavSame: ToolButton', 'FavNoOrphan: ToolButton', 'FavDiffNoOrphan: ToolButton', 'FavOrphan: ToolButton', 'FavLeftNewer: ToolButton', 'FavRightNewer: ToolButton', 'FavLeftNewerOrphan: ToolButton', 'FavRightNewerOrphan: ToolButton', 'FavLeftOrphan: ToolButton', 'FavRightOrphan: ToolButton', 'FavCompareNone: ToolButton', 'FavChanged: ToolButton', 'FavConflict: ToolButton', 'FavLeft: ToolButton', 'FavRight: ToolButton', 'FavMergeable: ToolButton', 'FavUnchanged: ToolButton', 'FavMergeNone: ToolButton', 'TogSame: ToolButton', 'TogLeftOrphan: ToolButton', 'TogRightOrphan: ToolButton', 'TogLeftNewer: ToolButton', 'TogRightNewer: ToolButton', 'TogDiff: ToolButton', 'TogNoMod: ToolButton', 'TogSameMod: ToolButton', 'TogLeftAdd: ToolButton', 'TogRightAdd: ToolButton', 'TogLeftDel: ToolButton', 'TogRightDel: ToolButton', 'TogLeftMod: ToolButton', 'TogRightMod: ToolButton', 'TogDiffMod: ToolButton', 'TogConflict: ToolButton', 'DirHandling: SeparatorButton', 'DirHandling: SubmenuButton', ('DirShowAll: MenuItem', 'DirCompareStructure: MenuItem', 'DirCompareFilesOnly: MenuItem', 'DirFlatten: MenuItem'), 'Actions: SeparatorButton', 'Compare: ToolButton', 'Merge: ToolButton', 'CopyRight: ToolButton', 'CopyLeft: ToolButton', 'CopyPrompt: ToolButton', 'CopySide: ToolButton', 'CopyToOutput: ToolButton', 'MoveRight: ToolButton', 'MoveLeft: ToolButton', 'MovePrompt: ToolButton', 'MoveSide: ToolButton', 'MoveBoth: ToolButton', 'CopyTo: ToolButton', 'MoveTo: ToolButton', 'Delete: ToolButton', 'Rename: ToolButton', 'Touch: ToolButton', 'NewFolder: ToolButton', 'Ignored: ToolButton', 'FileReport: ToolButton', 'Sync: SeparatorButton', 'UpdateRight: ToolButton', 'UpdateLeft: ToolButton', 'UpdateBoth: ToolButton', 'MirrorRight: ToolButton', 'MirrorLeft: ToolButton', 'SelectAll: ToolButton', 'SelectAllFiles: ToolButton', 'Search: SeparatorButton', 'DiffNext: ToolButton', 'DiffPrev: ToolButton', 'Info: ToolButton', 'MergeBaseView: ToolButton', 'SyncBaseView: ToolButton', 'Stop: ToolButton', 'View: SeparatorButton', 'ShowCenter: ToolButton', 'FileFilters: SeparatorButton', 'NameFilterEdit: ComboBox', 'NameFilter: ToolButton'), 'Tree: PopupMenu', ('OpenWithList: SubmenuItem', (), 'QuickCompare: MenuItem', 'CompareTo: MenuItem', 'AlignWith: MenuItem', 'N1: SeparatorItem', 'Compare: MenuItem', 'Merge: MenuItem', 'CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopyPrompt: MenuItem', 'CopySide: MenuItem', 'CopyToOutput: MenuItem', 'MoveRight: MenuItem', 'MoveLeft: MenuItem', 'MovePrompt: MenuItem', 'MoveSide: MenuItem', 'MoveBoth: MenuItem', 'CopyTo: MenuItem', 'MoveTo: MenuItem', 'Delete: MenuItem', 'Rename: MenuItem', 'Attributes: MenuItem', 'Touch: MenuItem', 'Exclude: MenuItem', 'NewFolder: MenuItem', 'CopyFilenames: MenuItem', 'Ignored: MenuItem', 'RefreshSelection: MenuItem', 'FileReport: MenuItem', 'N2: SeparatorItem', 'SyncList: SubmenuItem', ('UpdateRight: MenuItem', 'UpdateLeft: MenuItem', 'UpdateBoth: MenuItem', 'MirrorRight: MenuItem', 'MirrorLeft: MenuItem'), 'N3: SeparatorItem', 'SourceControlList: SubmenuItem', ('VcsAdd: MenuItem', 'VcsRemove: MenuItem', 'VcsGetLatest: MenuItem', 'VcsGet: MenuItem', 'N1: SeparatorItem', 'VcsCheckIn: MenuItem', 'VcsCheckOut: MenuItem', 'VcsUndoCheckOut: MenuItem', 'N2: SeparatorItem', 'VcsDiff: MenuItem', 'VcsHistory: MenuItem', 'VcsProperties: MenuItem', 'N3: SeparatorItem', 'VcsRunApp: MenuItem')))
  end
end
