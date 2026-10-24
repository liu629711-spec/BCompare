object HexActions: THexActions
  object List: TUiActionList
    object SelectAllAction: TUiAction
      Hint = 'Select All|Selects all visible bytes.'
    end
    object FileFormatAction: TUiAction
      ImageIndex = imgHexFormatEdit
    end
    object DiffItemNextAction: TUiAction
      Caption = '&Next Difference Bytes'
      Hint = 'Next Difference Bytes|Positions at next difference bytes.'
    end
    object DiffItemPrevAction: TUiAction
      Caption = '&Previous Difference Bytes'
      Hint = 'Previous Difference Bytes|Positions at previous difference bytes.'
    end
    object ExistsNextAction: TUiAction
      Hint = 'Next Existing Byte|Positions at next existing byte, skipping over gaps.'
    end
    object ExistsPrevAction: TUiAction
      Hint = 'Previous Existing Byte|Positions at previous existing byte, skipping over gaps.'
    end
    object FavCompareAllAction: TUiAction
      Hint = 'Show All|Shows same, left orphan, right orphan and difference bytes.'
    end
    object FavDiffAction: TUiAction
      Hint = 'Show Differences|Shows left orphan, right orphan and difference bytes.'
    end
    object FavSameAction: TUiAction
      Hint = 'Show Same|Shows same bytes.'
    end
    object CopyRightAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y to Right'
      Hint = 'Copy to Right|Copies selected or current bytes to right pane.'
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
      Hint = 'Copy to Left|Copies selected or current bytes to left pane.'
      ImageIndex = imgCopyLeft
      MacShortCutStr = 'Alt+Meta+Left'
      MenuAllowed = False
      ShortCaption = 'Copy'
      ShortCutStr = 'Ctrl+L'
      ToolbarAllowed = False
    end
    object CopySideAction: TUiAction
      Category = 'Edit'
      Hint = 'Copy to Other Side|Copies selected or current bytes to pane on other side.'
    end
    object DeleteAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete'
      Hint = 'Delete|Deletes selection.'
      ImageIndex = imgDelete
      ShortCaption = 'Delete'
      ToolbarAllowed = False
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
      Hint = 'Go To|Positions at specified byte.'
      ImageIndex = imgGoTo
      MacShortCutStr = 'Meta+L'
      ShortCaption = 'Go To'
      ShortCutStr = 'Ctrl+G'
      ToolbarAllowed = False
    end
    object ItemNumAction: TUiAction
      Category = 'View'
      Hint = 'Current Byte Address|Copies current byte address and puts it on Clipboard.'
    end
    object LittleEndianListAction: TUiAction
      Category = 'View'
      Caption = '&Little Endian Values'
      Hint = 'Little Endian Values|Displays little endian values in picked way.'
    end
    object BigEndianListAction: TUiAction
      Category = 'View'
      Caption = '&Big Endian Values'
      Hint = 'Big Endian Values|Displays big endian values in picked way.'
    end
    object ShowItemNumAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Byte &Addresses'
      Hint = 'Byte Addresses|Shows or hides byte addresses.'
      ImageIndex = imgShowItemNum
      ShortCaption = 'Byte #s'
      ToolbarAllowed = False
    end
    object LayoutAction: TUiAction
      Category = 'View'
      Caption = 'La&yout...'
      Hint = 'Layout|Configures layout options.'
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
    object OverwritingAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Hint = 'Overwrite|Typing replaces bytes instead of inserting them.'
      MacShortCutStr = 'Ins'
      ShortCutStr = 'Ins'
    end
  end
  object Tree: TUiActionTree
    Nodes = ('Edit: Menu', ('Redo: MenuItem', 'Sided: SeparatorItem', 'CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'Paste: MenuItem', 'Delete: MenuItem'), 'Search: Menu', ('Find: MenuItem', 'Replace: MenuItem', 'FindPrev: MenuItem', 'GoTo: SeparatorItem', 'GoTo: MenuItem'), 'View: Menu', ('SameModIgnored: MenuItem', 'ItemNum: SeparatorItem', 'ItemNum: MenuItem', 'LittleEndianList: SubmenuItem', (), 'BigEndianList: SubmenuItem', (), 'ShowWS: MenuItem', 'ShowItemNum: MenuItem', 'DisplayFontReset: MenuItem', 'Layout: MenuItem', 'OverUnder: MenuItem', 'ShowThumbnail: MenuItem'), 'Main: Toolbar', ('Redo: ToolButton', 'CopyRight: ToolButton', 'CopyLeft: ToolButton', 'CopySide: ToolButton', 'Cut: ToolButton', 'Copy: ToolButton', 'Paste: ToolButton', 'Delete: ToolButton', 'Find: ToolButton', 'Replace: ToolButton', 'FindPrev: ToolButton', 'GoTo: ToolButton', 'ShowWS: ToolButton', 'ShowItemNum: ToolButton', 'OverUnder: ToolButton', 'ShowThumbnail: ToolButton'), 'Edit: PopupMenu', ('CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'N1: SeparatorItem', 'Cut: MenuItem', 'Copy: MenuItem', 'Paste: MenuItem', 'Delete: MenuItem', 'N2: SeparatorItem', 'ItemNum: MenuItem', 'LittleEndianList: SubmenuItem', (), 'BigEndianList: SubmenuItem', (), 'N3: SeparatorItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenClipboard: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem'), 'Save: MenuItem', 'SaveAs: MenuItem', 'SaveAsLocal: MenuItem', 'SaveAsProfile: MenuItem', 'ExplorerList: SubmenuItem', ()))
  end
end
