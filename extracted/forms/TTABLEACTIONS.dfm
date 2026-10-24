object TableActions: TTableActions
  object List: TUiActionList
    object SelectAllAction: TUiAction
      Hint = 'Select All|Selects all visible rows.'
    end
    object FileFormatAction: TUiAction
      ImageIndex = imgTableFormatEdit
    end
    object DiffItemNextAction: TUiAction
      Caption = '&Next Difference Row'
      Hint = 'Next Difference Row|Positions at next difference row.'
    end
    object DiffItemPrevAction: TUiAction
      Caption = '&Previous Difference Row'
      Hint = 'Previous Difference Row|Positions at previous difference row.'
    end
    object ExistsNextAction: TUiAction
      Hint = 'Next Existing Row|Positions at next existing row, skipping over gaps.'
    end
    object ExistsPrevAction: TUiAction
      Hint = 'Previous Existing Row|Positions at previous existing row, skipping over gaps.'
    end
    object FavCompareAllAction: TUiAction
      Hint = 'Show All|Shows same, left orphan, right orphan and difference rows.'
    end
    object FavDiffAction: TUiAction
      Hint = 'Show Differences|Shows left orphan, right orphan and difference rows.'
    end
    object FavSameAction: TUiAction
      Hint = 'Show Same|Shows same rows.'
    end
    object FavCompareNoneAction: TUiAction
      Hint = 'Show None|Shows no rows.'
    end
    object TogSameAction: TUiAction
      Hint = 'Toggle Same|Shows or hides same rows.'
    end
    object TogLeftOrphanAction: TUiAction
      Hint = 'Toggle Left Orphans|Shows or hides left orphan rows.'
    end
    object TogRightOrphanAction: TUiAction
      Hint = 'Toggle Right Orphans|Shows or hides right orphan rows.'
    end
    object TogDiffAction: TUiAction
      Hint = 'Toggle Differences|Shows or hides difference rows.'
    end
    object AlignWithAction: TUiAction
      Category = 'Edit'
      Caption = 'Align &With...'
      Hint = 'Align With|Marks selected rows for manual realignment.'
      MacShortCutStr = 'Shift+Meta+A'
      ShortCutStr = 'F7'
    end
    object CopyRightAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y to Right'
      Hint = 'Copy to Right|Copies selected rows to right pane.'
      ImageIndex = imgCopyRight
      MacShortCutStr = 'Alt+Meta+Right'
      MenuAllowed = False
      ShortCaption = 'Copy'
      ShortCutStr = 'Ctrl+R'
      ToolbarAllowed = False
    end
    object CopyLeftAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y to Left'
      Hint = 'Copy to Left|Copies selected rows to left pane.'
      ImageIndex = imgCopyLeft
      MacShortCutStr = 'Alt+Meta+Left'
      MenuAllowed = False
      ShortCaption = 'Copy'
      ShortCutStr = 'Ctrl+L'
      ToolbarAllowed = False
    end
    object CopySideAction: TUiAction
      Category = 'Edit'
      Hint = 'Copy to Other Side|Copies selected rows to pane on other side.'
    end
    object CopyCellRightAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y Cells to Right'
      Hint = 'Copy Cells to Right|Copies selected cells to right pane.'
      MacShortCutStr = 'Ctrl+Meta+Right'
      MenuAllowed = False
      ShortCaption = 'Copy Cells'
      ShortCutStr = 'Shift+Ctrl+R'
      ToolbarAllowed = False
    end
    object CopyCellLeftAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y Cells to Left'
      Hint = 'Copy Cells to Left|Copies selected cells to left pane.'
      MacShortCutStr = 'Ctrl+Meta+Left'
      MenuAllowed = False
      ShortCaption = 'Copy Cells'
      ShortCutStr = 'Shift+Ctrl+L'
      ToolbarAllowed = False
    end
    object CopyCellSideAction: TUiAction
      Category = 'Edit'
      Hint = 'Copy Cells to Other Side|Copies selected cells to pane on other side.'
      ToolbarAllowed = False
    end
    object DeleteAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete'
      Hint = 'Delete|Deletes selection.'
      ImageIndex = imgDelete
      ShortCaption = 'Delete'
      ToolbarAllowed = False
    end
    object DeleteItemAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete Row'
      Hint = 'Delete Row|Deletes selected rows.'
    end
    object DeleteColAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete Column'
      Hint = 'Delete Column|Deletes selected columns.'
    end
    object InsertItemBeforeAction: TUiAction
      Category = 'Edit'
      Caption = 'Insert Row &Before'
      Hint = 'Insert Row Before|Inserts new rows before selected ones.'
      MacShortCutStr = 'Shift+Ctrl+Enter'
      ShortCutStr = 'Shift+Ctrl+Enter'
    end
    object InsertItemAfterAction: TUiAction
      Category = 'Edit'
      Caption = '&Insert Row After'
      Hint = 'Insert Row After|Inserts new rows after selected ones.'
      MacShortCutStr = 'Ctrl+Enter'
      ShortCutStr = 'Ctrl+Enter'
    end
    object InsertColBeforeAction: TUiAction
      Category = 'Edit'
      Caption = 'Insert Column B&efore'
      Hint = 'Insert Column Before|Inserts new columns before selected ones.'
    end
    object InsertColAfterAction: TUiAction
      Category = 'Edit'
      Caption = 'I&nsert Column After'
      Hint = 'Insert Column After|Inserts new columns after selected ones.'
    end
    object ModifyAction: TUiAction
      Category = 'Edit'
      Caption = '&Modify...'
      Hint = 'Modify|Modifies cell text.'
      MacShortCutStr = 'Alt+Enter'
      ShortCutStr = 'F2'
    end
    object SortAction: TUiAction
      Category = 'Edit'
      Caption = '&Sort...'
      Hint = 'Sort|Sorts selected data.'
    end
    object DiffNextAction: TUiAction
      Category = 'Search'
      Caption = 'Nex&t Difference Cell'
      Hint = 'Next Difference Cell|Positions at next difference cell.'
      MacShortCutStr = 'Ctrl+Alt+Down'
      ShortCutStr = 'Shift+Ctrl+N'
    end
    object DiffPrevAction: TUiAction
      Category = 'Search'
      Caption = 'Previo&us Difference Cell'
      Hint = 'Previous Difference Cell|Positions at previous difference cell.'
      MacShortCutStr = 'Ctrl+Alt+Up'
      ShortCutStr = 'Shift+Ctrl+P'
    end
    object DiffSheetNextAction: TUiAction
      Category = 'Search'
      Caption = 'Next Difference &Sheet'
      Hint = 'Next Difference Sheet|Positions at next difference sheet.'
    end
    object DiffSheetPrevAction: TUiAction
      Category = 'Search'
      Caption = 'Previous Difference S&heet'
      Hint = 'Previous Difference Sheet|Positions at previous difference sheet.'
    end
    object EditNextAction: TUiAction
      Category = 'Search'
      Caption = 'Next &Edit'
      Hint = 'Next Edit|Positions at next edited text.'
    end
    object EditPrevAction: TUiAction
      Category = 'Search'
      Caption = 'Previous E&dit'
      Hint = 'Previous Edit|Positions at previous edited text.'
    end
    object ReplaceAction: TUiAction
      Category = 'Search'
      Caption = '&Replace...'
      Hint = 'Replace|Replaces search string.'
      ImageIndex = imgReplace
      MacShortCutStr = 'Alt+Meta+F'
      ShortCaption = 'Replace'
      ShortCutStr = 'Ctrl+H'
      ToolbarAllowed = False
    end
    object GoToAction: TUiAction
      Category = 'Search'
      Caption = '&Go To...'
      Hint = 'Go To|Positions at specified row and column.'
      ImageIndex = imgGoTo
      MacShortCutStr = 'Meta+L'
      ShortCaption = 'Go To'
      ShortCutStr = 'Ctrl+G'
      ToolbarAllowed = False
    end
    object ColHideSameAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Hide Same Columns'
      Hint = 'Hide Same Columns|Hides same columns.'
    end
    object ColDetectSizeAction: TUiAction
      Category = 'View'
      Caption = '&Resize Columns to Fit'
      Hint = 'Resize Columns to Fit|Makes columns wide enough for data to be fully visible.'
    end
    object ShowItemNumAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Row &Numbers'
      Hint = 'Row Numbers|Shows or hides row numbers.'
      ImageIndex = imgShowItemNum
      ShortCaption = 'Row #s'
      ToolbarAllowed = False
    end
    object ShowThumbnailAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Thu&mbnail'
      Hint = 'Thumbnail|Shows or hides thumbnail view.'
      ImageIndex = imgShowThumbnail
      ShortCaption = 'Thumb'
      ToolbarAllowed = False
    end
    object ShowDetailsAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Text &Details'
      Hint = 'Text Details|Shows or hides text details panel.'
      ImageIndex = imgShowTextDetails
      ShortCaption = 'Details'
      ToolbarAllowed = False
    end
  end
  object Tree: TUiActionTree
    Nodes = ('Edit: Menu', ('Redo: MenuItem', 'Sided: SeparatorItem', 'AlignWith: MenuItem', 'CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'CopyCellRight: MenuItem', 'CopyCellLeft: MenuItem', 'CopyCellSide: MenuItem', 'Paste: MenuItem', 'Delete: MenuItem', 'DeleteItem: MenuItem', 'DeleteCol: MenuItem', 'InsertItemBefore: MenuItem', 'InsertItemAfter: MenuItem', 'InsertColBefore: MenuItem', 'InsertColAfter: MenuItem', 'Modify: MenuItem', 'Sort: MenuItem'), 'Search: Menu', ('DiffNext: MenuItem', 'DiffPrev: MenuItem', 'DiffItemPrev: MenuItem', 'DiffSheetNext: MenuItem', 'DiffSheetPrev: MenuItem', 'TakeFileRight: MenuItem', 'Edit: SeparatorItem', 'EditNext: MenuItem', 'EditPrev: MenuItem', 'Find: MenuItem', 'Replace: MenuItem', 'FindPrev: MenuItem', 'GoTo: SeparatorItem', 'GoTo: MenuItem'), 'View: Menu', ('SameModIgnored: MenuItem', 'Cols: SeparatorItem', 'ColHideSame: MenuItem', 'ColDetectSize: MenuItem', 'ShowWS: MenuItem', 'ShowItemNum: MenuItem', 'OverUnder: MenuItem', 'ShowThumbnail: MenuItem', 'ShowDetails: MenuItem'), 'Main: Toolbar', ('Redo: ToolButton', 'CopyRight: ToolButton', 'CopyLeft: ToolButton', 'CopySide: ToolButton', 'CopyCellRight: ToolButton', 'CopyCellLeft: ToolButton', 'CopyCellSide: ToolButton', 'Cut: ToolButton', 'Copy: ToolButton', 'Paste: ToolButton', 'Delete: ToolButton', 'Find: ToolButton', 'Replace: ToolButton', 'FindPrev: ToolButton', 'GoTo: ToolButton', 'ShowWS: ToolButton', 'ShowItemNum: ToolButton', 'OverUnder: ToolButton', 'ShowThumbnail: ToolButton', 'ShowDetails: ToolButton'), 'Edit: PopupMenu', ('AlignWith: MenuItem', 'CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'CopyCellRight: MenuItem', 'CopyCellLeft: MenuItem', 'CopyCellSide: MenuItem', 'N1: SeparatorItem', 'Cut: MenuItem', 'Copy: MenuItem', 'Paste: MenuItem', 'Delete: MenuItem', 'DeleteItem: MenuItem', 'DeleteCol: MenuItem', 'InsertItemBefore: MenuItem', 'InsertItemAfter: MenuItem', 'InsertColBefore: MenuItem', 'InsertColAfter: MenuItem', 'Modify: MenuItem', 'Sort: MenuItem', 'N2: SeparatorItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenClipboard: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem'), 'Save: MenuItem', 'SaveAs: MenuItem', 'SaveAsLocal: MenuItem', 'SaveAsProfile: MenuItem', 'ExplorerList: SubmenuItem', ()), 'DetailsEdit: PopupMenu', ('CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'CopyCellRight: MenuItem', 'CopyCellLeft: MenuItem', 'CopyCellSide: MenuItem', 'N1: SeparatorItem', 'Cut: MenuItem', 'Copy: MenuItem', 'Paste: MenuItem', 'Delete: MenuItem', 'Modify: MenuItem'), 'Header: PopupMenu', ('DeleteCol: MenuItem', 'InsertColBefore: MenuItem', 'InsertColAfter: MenuItem'), 'Gutter: PopupMenu', ('CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'CopyCellRight: MenuItem', 'CopyCellLeft: MenuItem', 'CopyCellSide: MenuItem', 'N1: SeparatorItem', 'DeleteItem: MenuItem', 'InsertItemBefore: MenuItem', 'InsertItemAfter: MenuItem', 'N2: SeparatorItem', 'ShowItemNum: MenuItem'))
  end
end
