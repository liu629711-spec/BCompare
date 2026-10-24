object RegActions: TRegActions
  object List: TUiActionList
    object SwapAction: TUiAction
      Hint = 'Swap Sides|Exchanges left, right registries.'
    end
    object ReloadAction: TUiAction
      Caption = '&Reload'
      Hint = 'Reload|Reloads displayed registries.'
    end
    object RecompareAction: TUiAction
      Caption = 'Reco&mpare'
      Hint = 'Recompare|Recompares displayed registries without reloading them.'
    end
    object OpenAction: TUiAction
      Caption = '&Open...'
      Hint = 'Open|Opens registry into picked pane.'
    end
    object OpenLocalAction: TUiAction
      Caption = 'Open Registry File on File S&ystem...'
      Hint = 'Open Registry File on File System|Opens existing local registry file into picked pane.'
    end
    object OpenProfileAction: TUiAction
      Caption = 'Open Registry File Using &Profile...'
      Hint = 'Open Registry File Using Profile|Opens existing registry file into picked pane using profile.'
    end
    object UpOneLevelListAction: TUiAction
      Category = 'Session'
      Caption = 'Up One Level'
      Hint = 'Up One Level|Changes base keys on picked sides to their parent keys.'
      ImageIndex = imgUpOneLevel
    end
    object UpOneLevelLeftAction: TUiAction
      Category = 'Session'
      Caption = '&Left Side'
      Hint = 'Up One Level on Left Side|Changes left base key to its parent key.'
    end
    object UpOneLevelRightAction: TUiAction
      Category = 'Session'
      Caption = '&Right Side'
      Hint = 'Up One Level on Right Side|Changes right base key to its parent key.'
    end
    object UpOneLevelBothAction: TUiAction
      Category = 'Session'
      Caption = '&Both Sides'
      Hint = 'Up One Level on Both Sides|Changes both base keys to their parent keys.'
    end
    object OpenRegAction: TUiAction
      Category = 'File'
      Caption = 'Open &Registry...'
      Hint = 'Open Registry|Opens live registry into picked pane.'
      MenuAllowed = False
    end
    object SetAsBasesAction: TUiAction
      Category = 'Edit'
      Hint = 'Set as Base Keys|Sets selected keys as base keys.'
    end
    object SetBothAsBasesAction: TUiAction
      Category = 'Edit'
      Caption = 'Set B&oth as Base Keys'
      Hint = 'Set Both as Base Keys|Sets selected key and key on other side as base keys.'
    end
    object SetAsOtherBaseAction: TUiAction
      Category = 'Edit'
      Caption = 'Set as Base Key on Ot&her Side'
      Hint = 'Set as Base Key on Other Side|Sets selected key as base key on other side.'
    end
    object CopyRightAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y to Right'
      Hint = 'Copy to Right|Copies selected items to right pane.'
      ImageIndex = imgCopyRight
      MenuAllowed = False
      ShortCaption = 'Copy'
      ShortCutStr = 'Ctrl+R'
      ToolbarAllowed = False
    end
    object CopyLeftAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y to Left'
      Hint = 'Copy to Left|Copies selected items to left pane.'
      ImageIndex = imgCopyLeft
      MenuAllowed = False
      ShortCaption = 'Copy'
      ShortCutStr = 'Ctrl+L'
      ToolbarAllowed = False
    end
    object CopySideAction: TUiAction
      Category = 'Edit'
      Hint = 'Copy to Other Side|Copies selected items to pane on other side.'
    end
    object DeleteAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete'
      Hint = 'Delete|Deletes selected items.'
      ImageIndex = imgDelete
      ShortCaption = 'Delete'
      ToolbarAllowed = False
    end
    object RenameAction: TUiAction
      Category = 'Edit'
      Caption = 'Re&name'
      Hint = 'Rename|Renames item.'
      ImageIndex = imgRename
      ShortCaption = 'Rename'
      ShortCutStr = 'F2'
      ToolbarAllowed = False
    end
    object NewKeyAction: TUiAction
      Category = 'Edit'
      Caption = 'New &Key'
      Hint = 'New Key|Adds a new key.'
    end
    object NewValAction: TUiAction
      Category = 'Edit'
      Caption = 'New &Value'
      Hint = 'New Value|Adds a new value.'
      ShortCutStr = 'Ins'
    end
    object ModifyAction: TUiAction
      Category = 'Edit'
      Caption = '&Modify...'
      Hint = 'Modify|Modifies value.'
    end
    object CopyKeyNameAction: TUiAction
      Category = 'Edit'
      Caption = '&Copy Key Name'
      Hint = 'Copy Key Name|Copies key''s name to Clipboard.'
    end
    object ExportKeyAction: TUiAction
      Category = 'Edit'
      Caption = '&Export...'
      Hint = 'Export|Saves key as registry file.'
    end
    object ExportAllAction: TUiAction
      Category = 'Edit'
      Caption = 'Export A&ll...'
      Hint = 'Export All|Saves all keys as registry file.'
    end
    object ExpandAllAction: TUiAction
      Category = 'View'
      Caption = '&Expand All'
      Hint = 'Expand All|Opens all items.'
      ImageIndex = imgExpandAll
      ShortCaption = 'Expand'
    end
    object CollapseAllAction: TUiAction
      Category = 'View'
      Caption = '&Collapse All'
      Hint = 'Collapse All|Closes all items.'
      ImageIndex = imgCollapseAll
      ShortCaption = 'Collapse'
    end
    object ShowTextDetailsAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Text &Details'
      Hint = 'Text Details|Shows or hides text details panel.'
      ImageIndex = imgShowTextDetails
      ShortCaption = 'Details'
      ToolbarAllowed = False
    end
    object ShowHexDetailsAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'He&x Details'
      Hint = 'Hex Details|Shows or hides hexadecimal details panel.'
      ImageIndex = imgShowHexDetails
      ShortCaption = 'Hex'
      ToolbarAllowed = False
    end
  end
  object Tree: TUiActionTree
    Nodes = ('Session: Menu', ('Swap: MenuItem', 'UpOneLevelList: SubmenuItem', ('UpOneLevelLeft: MenuItem', 'UpOneLevelRight: MenuItem', 'UpOneLevelBoth: MenuItem')), 'File: Menu', ('Open: MenuItem', 'OpenReg: MenuItem'), 'Edit: Menu', ('SetAsBases: MenuItem', 'SetBothAsBases: MenuItem', 'SetAsOtherBase: MenuItem', 'Undo: SeparatorItem', 'Redo: MenuItem', 'Sided: SeparatorItem', 'CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'Copy: MenuItem', 'Delete: MenuItem', 'Rename: MenuItem', 'NewKey: MenuItem', 'NewVal: MenuItem', 'Modify: MenuItem', 'Export: SeparatorItem', 'CopyKeyName: MenuItem', 'ExportKey: MenuItem', 'ExportAll: MenuItem'), 'View: Menu', ('SameModIgnored: MenuItem', 'Expanded: SeparatorItem', 'ExpandAll: MenuItem', 'CollapseAll: MenuItem', 'OverUnder: MenuItem', 'ShowTextDetails: MenuItem', 'ShowHexDetails: MenuItem'), 'Main: Toolbar', ('Redo: ToolButton', 'CopyRight: ToolButton', 'CopyLeft: ToolButton', 'CopySide: ToolButton', 'Copy: ToolButton', 'Delete: ToolButton', 'Rename: ToolButton', 'View: SeparatorButton', 'ExpandAll: ToolButton', 'CollapseAll: ToolButton', 'OverUnder: ToolButton', 'ShowTextDetails: ToolButton', 'ShowHexDetails: ToolButton'), 'Edit: PopupMenu', ('SetAsBases: MenuItem', 'SetBothAsBases: MenuItem', 'SetAsOtherBase: MenuItem', 'N1: SeparatorItem', 'CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'N2: SeparatorItem', 'Copy: MenuItem', 'Delete: MenuItem', 'Rename: MenuItem', 'NewKey: MenuItem', 'NewVal: MenuItem', 'Modify: MenuItem', 'N3: SeparatorItem', 'CopyKeyName: MenuItem', 'ExportKey: MenuItem', 'N4: SeparatorItem', 'Open: MenuItem', 'OpenReg: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem'), 'ExplorerList: SubmenuItem', ()), 'DetailsEdit: PopupMenu', ('CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'N1: SeparatorItem', 'Copy: MenuItem', 'Modify: MenuItem'))
  end
end
