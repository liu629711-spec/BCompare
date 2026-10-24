object DirBaseActions: TDirBaseActions
  object List: TUiActionList
    object SelectAllAction: TUiAction
      ImageIndex = imgSelectAll
      ShortCaption = 'Select'
    end
    object SwapAction: TUiAction
      Hint = 'Swap Sides|Exchanges left, right base folders.'
    end
    object BrowseListAction: TUiAction
      Category = 'Session'
      Caption = 'B&rowse for Folder'
      Hint = 'Browse for Folder|Browses for an existing folder on picked side.'
      ImageIndex = imgBrowse
    end
    object BrowseLeftAction: TUiAction
      Category = 'Session'
      Caption = '&Left Side'
      Hint = 'Browse for Folder on Left Side|Browses for an existing folder on left side.'
    end
    object BrowseCenterAction: TUiAction
      Category = 'Session'
      Caption = '&Center Side'
      Hint = 'Browse for Folder on Center Side|Browses for an existing folder on center side.'
    end
    object BrowseRightAction: TUiAction
      Category = 'Session'
      Caption = '&Right Side'
      Hint = 'Browse for Folder on Right Side|Browses for an existing folder on right side.'
    end
    object BrowseOutputAction: TUiAction
      Category = 'Session'
      Caption = '&Output Side'
      Hint = 'Browse for Folder on Output Side|Browses for an existing folder on output side.'
    end
    object StopAction: TUiAction
      Category = 'Session'
      Hint = 'Stop Loading|Terminates comparison.'
      ImageIndex = imgStopRed
      ShortCaption = 'Stop'
    end
    object ExpandAction: TUiAction
      Category = 'Actions'
      Caption = 'Open Folder'
      Hint = 'Open Folder|Opens selected folder.'
    end
    object CollapseAction: TUiAction
      Category = 'Actions'
      Caption = 'Close Folder'
      Hint = 'Close Folder|Closes selected folder.'
    end
    object ExpandSubfoldersAction: TUiAction
      Category = 'Actions'
      Caption = 'Open Subfolders'
      Hint = 'Open Subfolders|Opens selected folders and all their subfolders.'
    end
    object CollapseSubfoldersAction: TUiAction
      Category = 'Actions'
      Caption = 'Close Subfolders'
      Hint = 'Close Subfolders|Closes selected folders and their subfolders.'
    end
    object SetAsBaseFoldersAction: TUiAction
      Category = 'Actions'
      Hint = 'Set as Base Folders|Sets selected folders as base folders.'
    end
    object SetAsOtherBaseFolderAction: TUiAction
      Category = 'Actions'
      Caption = 'Set as Base on Ot&her Side'
      Hint = 'Set as Base on Other Side|Sets selected folder as base folder on other side.'
    end
    object OpenAction: TUiAction
      Category = 'Actions'
      Hint = 'Open|Opens selected items in new view.'
    end
    object OpenWithListAction: TUiAction
      Category = 'Actions'
      Caption = 'Open &With'
      Hint = 'Open With|Opens selected items in new view of picked type.'
    end
    object AssocAppAction: TUiAction
      Category = 'Actions'
      Caption = 'Associated Application'
      Hint = 'Associated Application|Opens selected items with associated application.'
    end
    object RevealInFinderAction: TUiAction
      Category = 'Actions'
      Caption = 'Reveal in Finder'
      Hint = 'Reveal in Finder|Shows Finder and selects the picked file.'
    end
    object ExcludeAction: TUiAction
      Category = 'Actions'
      Caption = '&Exclude'
      Hint = 'Exclude|Filters selected items to remove them from comparison.'
    end
    object CopyFilenamesAction: TUiAction
      Category = 'Actions'
      Caption = 'Copy F&ilename'
      Hint = 'Copy Filename|Copies selected items'' paths to Clipboard.'
    end
    object RefreshSelectionAction: TUiAction
      Category = 'Actions'
      Caption = 'Refresh &Selection'
      Hint = 'Refresh Selection|Refreshes selected items.'
      MacShortCutStr = 'Alt+Meta+R'
      ShortCutStr = 'Shift+F5'
    end
    object ExplorerListAction: TUiAction
      Category = 'Actions'
      Caption = 'E&xplorer'
      Hint = 'Explorer|Shows Windows Explorer context menu for selected items.'
    end
    object ExpandAllAction: TUiAction
      Category = 'Edit'
      Caption = '&Expand All'
      Hint = 'Expand All|Opens all folders.'
      ImageIndex = imgExpandAll
      ShortCaption = 'Expand'
    end
    object CollapseAllAction: TUiAction
      Category = 'Edit'
      Caption = '&Collapse All'
      Hint = 'Collapse All|Closes all folders.'
      ImageIndex = imgCollapseAll
      ShortCaption = 'Collapse'
    end
    object SelectInvertAction: TUiAction
      Category = 'Edit'
      Caption = '&Invert Selection'
      Hint = 'Invert Selection|Selects all items not currently selected, and deselects all items currently selected.'
    end
    object RefreshAction: TUiAction
      Category = 'Edit'
      Caption = '&Refresh'
      Hint = 'Refresh|Refreshes open folders.'
      ImageIndex = imgRefresh
      MacShortCutStr = 'Meta+R'
      ShortCaption = 'Refresh'
      ShortCutStr = 'F5'
    end
    object FullRefreshAction: TUiAction
      Category = 'Edit'
      Caption = 'F&ull Refresh'
      Hint = 'Full Refresh|Refreshes entire comparison.'
      ImageIndex = imgFullRefresh
      MacShortCutStr = 'Shift+Meta+R'
      ShortCaption = 'Full Refresh'
      ShortCutStr = 'Ctrl+F5'
      ToolbarAllowed = False
    end
    object ExistsNextAction: TUiAction
      Category = 'Search'
      Hint = 'Next Existing Filename|Positions at next filename, skipping over gaps.'
      MacShortCutStr = 'Ctrl+Down'
      ShortCutStr = 'Alt+Down'
    end
    object ExistsPrevAction: TUiAction
      Category = 'Search'
      Hint = 'Previous Existing Filename|Positions at previous filename, skipping over gaps.'
      MacShortCutStr = 'Ctrl+Up'
      ShortCutStr = 'Alt+Up'
    end
    object FindFilenameAction: TUiAction
      Category = 'Search'
      Caption = '&Find Filename...'
      Hint = 'Find Filename|Finds filename matching search string.'
      ImageIndex = imgFind
      MacShortCutStr = 'Meta+F'
      ShortCaption = 'Find Filename'
      ShortCutStr = 'Ctrl+F'
      ToolbarAllowed = False
    end
    object FindFilenameNextAction: TUiAction
      Category = 'Search'
      Caption = 'Find Ne&xt Filename'
      Hint = 'Find Next Filename|Finds next filename matching search string.'
      ImageIndex = imgFindNext
      MacShortCutStr = 'Meta+G'
      ShortCaption = 'Next Filename'
      ShortCutStr = 'F3'
      ToolbarAllowed = False
    end
    object FindFilenamePrevAction: TUiAction
      Category = 'Search'
      Caption = 'Find Pre&vious Filename'
      Hint = 'Find Previous Filename|Finds previous filename matching search string.'
      ImageIndex = imgFindPrev
      MacShortCutStr = 'Shift+Meta+G'
      ShortCaption = 'Prev Filename'
      ShortCutStr = 'Shift+F3'
      ToolbarAllowed = False
    end
    object SuppressFiltersAction: TUiAction
      Category = 'View'
      Caption = '&Suppress Filters'
      Hint = 'Suppress Filters|Temporarily suppresses display and file filters.'
      ImageIndex = imgSuppressFilters
      ShortCaption = 'Peek'
    end
    object ColListAction: TUiAction
      Category = 'View'
      Caption = '&Columns'
      Hint = 'Columns|Shows or hides picked column.'
      DynVisible = True
    end
    object LegendAction: TUiAction
      Category = 'View'
      Caption = '&Legend'
      Hint = 'Legend|Shows or hides legend window.'
      MacShortCutStr = 'Alt+Meta+L'
      ShortCutStr = 'Ctrl+Alt+L'
    end
    object ShowLogAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'L&og'
      Hint = 'Log|Shows or hides log panel.'
    end
  end
  object Tree: TUiActionTree
    Nodes = ('Session: Menu', ('Swap: MenuItem', 'BrowseList: SubmenuItem', ('BrowseLeft: MenuItem', 'BrowseCenter: MenuItem', 'BrowseRight: MenuItem', 'BrowseOutput: MenuItem')), 'Actions: Menu', ('Expand: MenuItem', 'Collapse: MenuItem', 'ExpandSubfolders: MenuItem', 'CollapseSubfolders: MenuItem', 'SetAsBaseFolders: MenuItem', 'SetAsOtherBaseFolder: MenuItem', 'Open: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem', 'OpenTextPatch: MenuItem', 'N2: SeparatorItem', 'OpenDirCompare: MenuItem', 'OpenDirMerge: MenuItem', 'OpenDirSync: MenuItem', 'OpenTextCompare: MenuItem', 'OpenTextMerge: MenuItem', 'OpenHexCompare: MenuItem', 'OpenMediaCompare: MenuItem', 'OpenPixCompare: MenuItem', 'OpenRegCompare: MenuItem', 'OpenTableCompare: MenuItem', 'OpenVerCompare: MenuItem', 'OpenXMLCompare: MenuItem'), 'Common: SeparatorItem', 'Exclude: MenuItem', 'CopyFilenames: MenuItem', 'RefreshSelection: MenuItem', 'Last: SeparatorItem', 'ExplorerList: SubmenuItem', ()), 'Edit: Menu', ('Paste: MenuItem', 'Expand: SeparatorItem', 'ExpandAll: MenuItem', 'CollapseAll: MenuItem', 'SelectAll: MenuItem', 'SelectInvert: MenuItem', 'Refresh: MenuItem', 'FullRefresh: MenuItem'), 'Search: Menu', ('FindFilename: MenuItem', 'FindFilenameNext: MenuItem', 'FindFilenamePrev: MenuItem'), 'View: Menu', ('SameModIgnored: MenuItem', 'SuppressFilters: MenuItem', 'Layout: SeparatorItem', 'ColList: SubmenuItem', (), 'Legend: MenuItem', 'ShowLog: MenuItem'), 'Main: Toolbar', ('Rules: ToolButton', 'Actions: SeparatorButton', 'Edit: SeparatorButton', 'ExpandAll: ToolButton', 'CollapseAll: ToolButton', 'SelectAll: ToolButton', 'Refresh: ToolButton', 'FullRefresh: ToolButton', 'Search: SeparatorButton', 'FindFilename: ToolButton', 'FindFilenameNext: ToolButton', 'FindFilenamePrev: ToolButton', 'Info: ToolButton', 'Stop: ToolButton', 'FileFilters: SeparatorButton', 'SuppressFilters: ToolButton'), 'Tree: PopupMenu', ('Expand: MenuItem', 'Collapse: MenuItem', 'ExpandSubfolders: MenuItem', 'CollapseSubfolders: MenuItem', 'SetAsBaseFolders: MenuItem', 'SetAsOtherBaseFolder: MenuItem', 'Open: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem', 'OpenTextPatch: MenuItem', 'N2: SeparatorItem', 'OpenDirCompare: MenuItem', 'OpenDirMerge: MenuItem', 'OpenDirSync: MenuItem', 'OpenTextCompare: MenuItem', 'OpenTextMerge: MenuItem', 'OpenHexCompare: MenuItem', 'OpenMediaCompare: MenuItem', 'OpenPixCompare: MenuItem', 'OpenRegCompare: MenuItem', 'OpenTableCompare: MenuItem', 'OpenVerCompare: MenuItem', 'OpenXMLCompare: MenuItem'), 'N1: SeparatorItem', 'Exclude: MenuItem', 'CopyFilenames: MenuItem', 'RefreshSelection: MenuItem', 'N2: SeparatorItem', 'ExplorerList: SubmenuItem', ()))
  end
end
