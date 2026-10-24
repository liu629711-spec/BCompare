object FileActions: TFileActions
  object List: TUiActionList
    object FileFormatAction: TUiAction
      Category = 'Session'
      Hint = 'Format|Edits current File Format.'
      ShortCaption = 'Format'
    end
    object ReloadAction: TUiAction
      Category = 'Session'
      Caption = '&Reload Files'
      Hint = 'Reload Files|Reloads displayed files.'
      ImageIndex = imgRefresh
      MacShortCutStr = 'Meta+R'
      ShortCaption = 'Reload'
      ShortCutStr = 'F5'
    end
    object RecompareAction: TUiAction
      Category = 'Session'
      Caption = 'Reco&mpare Files'
      Hint = 'Recompare Files|Recompares displayed files without reloading them.'
      ImageIndex = imgRecompare
      MacShortCutStr = 'Shift+Meta+R'
      ShortCaption = 'Recompare'
      ShortCutStr = 'Ctrl+F5'
      ToolbarAllowed = False
    end
    object CompareUsingViewListAction: TUiAction
      Category = 'Session'
      Caption = 'Compare Files &Using'
      Hint = 'Compare Files Using|Compares files in picked new view.'
    end
    object MergeViewAction: TUiAction
      Category = 'Session'
      Caption = 'Mer&ge Files'
      Hint = 'Merge Files|Merges files in new view.'
      ShortCaption = 'Merge'
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
    object OpenAction: TUiAction
      Category = 'File'
      Caption = '&Open File...'
      Hint = 'Open File|Opens existing file into picked pane.'
      ImageIndex = imgBrowse
      MacShortCutStr = 'Meta+O'
      ShortCutStr = 'Ctrl+O'
    end
    object OpenLocalAction: TUiAction
      Category = 'File'
      Caption = 'Open File on File S&ystem...'
      Hint = 'Open File on File System|Opens existing local file into picked pane.'
      MenuAllowed = False
    end
    object OpenProfileAction: TUiAction
      Category = 'File'
      Caption = 'Open File Using &Profile...'
      Hint = 'Open File Using Profile|Opens existing file into picked pane using profile.'
      MenuAllowed = False
    end
    object OpenClipboardAction: TUiAction
      Category = 'File'
      Caption = 'Open &Clipboard'
      Hint = 'Open Clipboard|Opens Clipboard contents into picked pane.'
      MacShortCutStr = 'Shift+Meta+V'
      ShortCutStr = 'Shift+Ctrl+V'
    end
    object OpenWithListAction: TUiAction
      Category = 'File'
      Caption = 'Open &With'
      Hint = 'Open With|Opens picked file with picked application.'
    end
    object AssocAppAction: TUiAction
      Category = 'File'
      Caption = 'Associated Application'
      Hint = 'Associated Application|Opens picked file with associated application.'
    end
    object RevealInFinderAction: TUiAction
      Category = 'File'
      Caption = 'Reveal in Finder'
      Hint = 'Reveal in Finder|Shows Finder and selects the picked file.'
    end
    object SaveAction: TUiAction
      Category = 'File'
      Caption = '&Save File'
      Hint = 'Save File|Saves picked file which has been modified.'
      ImageIndex = imgSave
      MacShortCutStr = 'Meta+S'
      ShortCutStr = 'Ctrl+S'
    end
    object SaveAsAction: TUiAction
      Category = 'File'
      Caption = 'Save File &As...'
      Hint = 'Save File As|Saves picked file with new name.'
      MacShortCutStr = 'Shift+Meta+S'
      ShortCutStr = 'F12'
    end
    object SaveAsLocalAction: TUiAction
      Category = 'File'
      Caption = 'Save File on Fi&le System As...'
      Hint = 'Save File on File System As|Saves picked file with new name on file system.'
      MenuAllowed = False
    end
    object SaveAsProfileAction: TUiAction
      Category = 'File'
      Caption = 'Save File Using Pro&file As...'
      Hint = 'Save File Using Profile As|Saves picked file with new name using profile.'
      MenuAllowed = False
    end
    object ExplorerListAction: TUiAction
      Category = 'File'
      Caption = 'E&xplorer'
      Hint = 'Explorer|Shows Windows Explorer context menu for picked file.'
    end
    object DiffItemNextAction: TUiAction
      Category = 'Search'
      Caption = '&Next Difference Item'
      Hint = 'Next Difference Item|Positions at next difference item.'
      ImageIndex = imgDown
      MacShortCutStr = 'Alt+Down'
      ShortCaption = 'Next Diff'
      ShortCutStr = 'Ctrl+N'
    end
    object DiffItemPrevAction: TUiAction
      Category = 'Search'
      Caption = '&Previous Difference Item'
      Hint = 'Previous Difference Item|Positions at previous difference item.'
      ImageIndex = imgUp
      MacShortCutStr = 'Alt+Up'
      ShortCaption = 'Prev Diff'
      ShortCutStr = 'Ctrl+P'
    end
    object DiffFileNextAction: TUiAction
      Category = 'Search'
      Caption = 'Next D&ifference Files'
      Hint = 'Next Difference Files|Opens folder compare''s next difference files.'
      ImageIndex = imgDiffFileNext
      MacShortCutStr = 'Alt+Meta+Down'
      ShortCaption = 'Next File'
      ShortCutStr = 'Ctrl+M'
      ToolbarAllowed = False
    end
    object DiffFilePrevAction: TUiAction
      Category = 'Search'
      Caption = 'Previ&ous Difference Files'
      Hint = 'Previous Difference Files|Opens folder compare''s previous difference files.'
      ImageIndex = imgDiffFilePrev
      MacShortCutStr = 'Alt+Meta+Up'
      ShortCaption = 'Prev File'
      ShortCutStr = 'Shift+Ctrl+M'
      ToolbarAllowed = False
    end
    object CopyFileRightAction: TUiAction
      Category = 'Search'
      Caption = '&Copy File to Right and Open Next Difference'
      Hint = 'Copy File to Right and Open Next Difference|Copies left file to right and opens folder compare''s next difference.'
      ImageIndex = imgCopyFileRight
      MacShortCutStr = 'Ctrl+Alt+Right'
      ShortCaption = 'Copy File'
      ShortCutStr = 'Ctrl+Alt+R'
      ToolbarAllowed = False
    end
    object CopyFileLeftAction: TUiAction
      Category = 'Search'
      Caption = 'Cop&y File to Left and Open Next Difference'
      Hint = 'Copy File to Left and Open Next Difference|Copies right file to left and opens folder compare''s next difference.'
      ImageIndex = imgCopyFileLeft
      MacShortCutStr = 'Ctrl+Alt+Left'
      ShortCaption = 'Copy File'
      ShortCutStr = 'Ctrl+Alt+L'
      ToolbarAllowed = False
    end
    object TakeFileLeftAction: TUiAction
      Category = 'Search'
      Caption = 'Take Left File and Open Next Difference'
      Hint = 'Take Left File and Open Next Difference|Takes left file and opens folder merge''s next difference.'
      ImageIndex = imgCopyFileRight
      MacShortCutStr = 'Ctrl+Alt+Left'
      ShortCaption = 'Take File'
      ShortCutStr = 'Ctrl+Alt+L'
      ToolbarAllowed = False
    end
    object TakeFileRightAction: TUiAction
      Category = 'Search'
      Caption = 'Take Right File and Open Next Difference'
      Hint = 'Take Right File and Open Next Difference|Takes right file and opens folder merge''s next difference.'
      ImageIndex = imgCopyFileLeft
      MacShortCutStr = 'Ctrl+Alt+Right'
      ShortCaption = 'Take File'
      ShortCutStr = 'Ctrl+Alt+R'
      ToolbarAllowed = False
    end
    object ExistsNextAction: TUiAction
      Category = 'Search'
      Hint = 'Next Existing Item|Positions at next item, skipping over gaps.'
      MacShortCutStr = 'Ctrl+Down'
      ShortCutStr = 'Alt+Down'
    end
    object ExistsPrevAction: TUiAction
      Category = 'Search'
      Hint = 'Previous Existing Item|Positions at previous item, skipping over gaps.'
      MacShortCutStr = 'Ctrl+Up'
      ShortCutStr = 'Alt+Up'
    end
    object FindAction: TUiAction
      Category = 'Search'
      Caption = '&Find...'
      Hint = 'Find|Finds search string.'
      ImageIndex = imgFind
      MacShortCutStr = 'Meta+F'
      ShortCaption = 'Find'
      ShortCutStr = 'Ctrl+F'
      ToolbarAllowed = False
    end
    object FindNextAction: TUiAction
      Category = 'Search'
      Caption = 'Find Ne&xt'
      Hint = 'Find Next|Finds next occurrence of search string.'
      ImageIndex = imgFindNext
      MacShortCutStr = 'Meta+G'
      ShortCaption = 'Next'
      ShortCutStr = 'F3'
      ToolbarAllowed = False
    end
    object FindPrevAction: TUiAction
      Category = 'Search'
      Caption = 'Find Pre&vious'
      Hint = 'Find Previous|Finds previous occurrence of search string.'
      ImageIndex = imgFindPrev
      MacShortCutStr = 'Shift+Meta+G'
      ShortCaption = 'Prev'
      ShortCutStr = 'Shift+F3'
      ToolbarAllowed = False
    end
    object GoLeftAction: TUiAction
      Category = 'Search'
      Hint = 'Go Left|Positions in pane left of current one.'
      MacShortCutStr = 'Shift+Ctrl+Left'
      ShortCutStr = 'Alt+Left'
    end
    object GoRightAction: TUiAction
      Category = 'Search'
      Hint = 'Go Right|Positions in pane right of current one.'
      MacShortCutStr = 'Shift+Ctrl+Right'
      ShortCutStr = 'Alt+Right'
    end
    object GoNextAction: TUiAction
      Category = 'Search'
      Hint = 'Go Next|Positions in pane after current one.'
      MacShortCutStr = 'F6'
      ShortCutStr = 'F6'
    end
    object GoPrevAction: TUiAction
      Category = 'Search'
      Hint = 'Go Prev|Positions in pane before current one.'
      MacShortCutStr = 'Shift+F6'
      ShortCutStr = 'Shift+F6'
    end
    object FavCompareAllAction: TUiAction
      Category = 'Favorites'
      Caption = 'Show All'
      Hint = 'Show All|Shows same, left orphan, right orphan and difference items.'
      ImageIndex = imgFavAll
      MacShortCutStr = 'Meta+1'
      ShortCaption = 'All'
    end
    object FavDiffAction: TUiAction
      Category = 'Favorites'
      Caption = 'Show Differences'
      Hint = 'Show Differences|Shows left orphan, right orphan and difference items.'
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
    object FavCompareNoneAction: TUiAction
      Category = 'View'
      Caption = 'Show None'
      Hint = 'Show None|Shows no items.'
      ImageIndex = imgFavNone
      MacShortCutStr = 'Meta+4'
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
      ShortCaption = 'Left'
    end
    object TogRightOrphanAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Right Orphans|Shows or hides right orphan items.'
      ShortCaption = 'Right'
    end
    object TogDiffAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Differences|Shows or hides difference items.'
      ShortCaption = 'Diffs'
    end
    object ShowWSAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Visible &Whitespace'
      Hint = 'Visible Whitespace|Shows or hides visible spaces, tabs.'
      ImageIndex = imgShowWS
      ShortCaption = 'Space'
      ToolbarAllowed = False
    end
    object DisplayFontAction: TUiAction
      Category = 'View'
      Caption = 'Display &Font...'
      ImageIndex = imgDisplayFont
      MenuAllowed = False
      ShortCaption = 'Font'
      ToolbarAllowed = False
    end
    object DisplayFontIncreaseAction: TUiAction
      Category = 'View'
      Caption = 'Increase Display Font Size'
      ImageIndex = imgDisplayFontIncrease
      MacSecondaryShortCutStr = 'Meta+='
      MacShortCutStr = 'Meta++'
      MenuAllowed = False
      SecondaryShortCutStr = 'Ctrl+='
      ShortCaption = '+Font'
      ShortCutStr = 'Ctrl+Num +'
      ToolbarAllowed = False
    end
    object DisplayFontDecreaseAction: TUiAction
      Category = 'View'
      Caption = 'Decrease Display Font Size'
      ImageIndex = imgDisplayFontDecrease
      MacShortCutStr = 'Meta+-'
      MenuAllowed = False
      SecondaryShortCutStr = 'Ctrl+-'
      ShortCaption = '-Font'
      ShortCutStr = 'Ctrl+Num -'
      ToolbarAllowed = False
    end
    object DisplayFontResetAction: TUiAction
      Category = 'View'
      Caption = 'Reset Display Font Size'
      ImageIndex = imgDisplayFontReset
      MenuAllowed = False
      ShortCaption = 'Font0'
      ShortCutStr = 'Ctrl+Num 0'
      ToolbarAllowed = False
    end
    object SideBySideAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Side-by-Side Layout'
      GroupIndex = 20
      Hint = 'Side-by-Side Layout|Arranges panes left and right of each other.'
      ImageIndex = imgSideBySide
      ShortCaption = 'Normal'
      ToolbarAllowed = False
    end
    object OverUnderAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Over-Under Layout'
      GroupIndex = 20
      Hint = 'Over-Under Layout|Arranges panes above and below each other.'
      ImageIndex = imgOverUnder
      ShortCaption = 'Stacked'
      ToolbarAllowed = False
    end
    object ShowSpecInfoAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'File &Info'
      Hint = 'File Info|Shows or hides file information.'
      ImageIndex = imgInfo
      ShortCaption = 'Info'
      ToolbarAllowed = False
    end
  end
  object Tree: TUiActionTree
    Nodes = ('Session: Menu', ('Swap: MenuItem', 'Reload: MenuItem', 'Recompare: MenuItem', 'Views: SeparatorItem', 'CompareUsingViewList: SubmenuItem', ('CompareUsingTextCompare: MenuItem', 'CompareUsingHexCompare: MenuItem', 'CompareUsingMediaCompare: MenuItem', 'CompareUsingPixCompare: MenuItem', 'CompareUsingRegCompare: MenuItem', 'CompareUsingTableCompare: MenuItem', 'CompareUsingVerCompare: MenuItem', 'CompareUsingXMLCompare: MenuItem'), 'MergeView: MenuItem', 'CompareToOutputList: SubmenuItem', ('CompareLeftToOutput: MenuItem', 'CompareCenterToOutput: MenuItem', 'CompareRightToOutput: MenuItem')), 'File: Menu', ('Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenClipboard: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem', 'OpenTextPatch: MenuItem'), 'Save: MenuItem', 'SaveAs: MenuItem', 'SaveAsLocal: MenuItem', 'SaveAsProfile: MenuItem', 'ExplorerList: SubmenuItem', ()), 'MergeFile: Menu', ('Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenClipboard: MenuItem', 'Save: MenuItem', 'SaveAs: MenuItem', 'SaveAsLocal: MenuItem', 'SaveAsProfile: MenuItem', 'ExplorerList: SubmenuItem', (), 'Settings: SeparatorItem', 'Swap: MenuItem', 'Reload: MenuItem', 'Recompare: MenuItem'), 'Edit: Menu', (), 'Search: Menu', ('DiffItemNext: MenuItem', 'DiffItemPrev: MenuItem', 'DiffFileNext: MenuItem', 'DiffFilePrev: MenuItem', 'CopyFileRight: MenuItem', 'CopyFileLeft: MenuItem', 'TakeFileLeft: MenuItem', 'TakeFileRight: MenuItem', 'Find: SeparatorItem', 'Find: MenuItem', 'FindNext: MenuItem', 'FindPrev: MenuItem'), 'View: Menu', ('FavCompareAll: MenuItem', 'FavDiff: MenuItem', 'FavSame: MenuItem', 'FavCompareNone: MenuItem', 'InsigIgnored: SeparatorItem', 'SameModIgnored: MenuItem', 'Display: SeparatorItem', 'ShowWS: MenuItem', 'DisplayFont: MenuItem', 'DisplayFontIncrease: MenuItem', 'DisplayFontDecrease: MenuItem', 'DisplayFontReset: MenuItem', 'Layout: SeparatorItem', 'SideBySide: MenuItem', 'OverUnder: MenuItem', 'ShowSpecInfo: MenuItem'), 'Main: Toolbar', ('SessionLocked: ToolButton', 'DisplayFilters: SeparatorButton', 'FavCompareAll: ToolButton', 'FavDiff: ToolButton', 'FavSame: ToolButton', 'FavCompareNone: ToolButton', 'TogSame: ToolButton', 'TogLeftOrphan: ToolButton', 'TogRightOrphan: ToolButton', 'TogDiff: ToolButton', 'Rules: ToolButton', 'FileFormat: SubmenuButton', (), 'Edit: SeparatorButton', 'Undo: ToolButton', 'Redo: ToolButton', 'Copy: ToolButton', 'Search: SeparatorButton', 'DiffItemNext: ToolButton', 'DiffItemPrev: ToolButton', 'DiffFileNext: ToolButton', 'DiffFilePrev: ToolButton', 'CopyFileRight: ToolButton', 'CopyFileLeft: ToolButton', 'TakeFileLeft: ToolButton', 'TakeFileRight: ToolButton', 'Find: ToolButton', 'FindNext: ToolButton', 'FindPrev: ToolButton', 'Swap: ToolButton', 'Reload: ToolButton', 'Recompare: ToolButton', 'Info: ToolButton', 'MergeView: ToolButton', 'View: SeparatorButton', 'ShowWS: ToolButton', 'DisplayFont: SubmenuButton', (), 'DisplayFontIncrease: ToolButton', 'DisplayFontDecrease: ToolButton', 'DisplayFontReset: ToolButton', 'SideBySide: ToolButton', 'OverUnder: ToolButton', 'ShowSpecInfo: ToolButton'))
  end
end
