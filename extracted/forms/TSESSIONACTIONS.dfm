object SessionActions: TSessionActions
  object List: TUiActionList
    object SessionHomeAction: TUiAction
      Category = 'Session'
      Hint = 'Home|Replaces current view with Home view.'
      ImageIndex = imgSessionHome
      MacShortCutStr = 'Shift+Meta+Home'
      Scope = 'Session'
      ShortCaption = 'Home'
      ShortCutStr = 'Alt+Home'
    end
    object SessionsComboAction: TUiAction
      Category = 'Session'
      Hint = 'Sessions Button|Focuses on dropdown button listing sessions that can be opened in this view.'
      ImageIndex = imgSessionsCombo
      Scope = 'Session'
      ShortCaption = 'Sessions'
    end
    object SessionSaveAction: TUiAction
      Category = 'Session'
      Caption = '&Save Session'
      Hint = 'Save Session|Saves this session.'
      ImageIndex = imgSessionSave
      MacShortCutStr = 'Ctrl+Meta+S'
      Scope = 'Session'
      ShortCaption = 'Save'
      ShortCutStr = 'Shift+Ctrl+S'
      ToolbarAllowed = False
    end
    object SessionSaveAsAction: TUiAction
      Category = 'Session'
      Caption = 'Save Session &As...'
      Hint = 'Save Session As|Saves this session with new name.'
      ImageIndex = imgSessionSaveAs
      Scope = 'Session'
      ShortCaption = 'Save As'
      ToolbarAllowed = False
    end
    object SessionEditAction: TUiAction
      Category = 'Session'
      Caption = 'S&ession Settings...'
      Hint = 'Session Settings|Edits current session settings.'
      ImageIndex = imgSessionEdit
      Scope = 'Session'
    end
    object SessionLockedAction: TUiAction
      Category = 'Session'
      Caption = '&Locked'
      Hint = 'Locked|Locks or unlocks current session.'
      ImageIndex = imgSessionLocked
      Scope = 'Session'
      ShortCaption = 'Locked'
      ToolbarAllowed = False
    end
    object SessionClearAction: TUiAction
      Category = 'Session'
      Caption = '&Clear Session'
      Hint = 'Clear Session|Replaces current view with empty session.'
      MacShortCutStr = 'Ctrl+Meta+C'
      Scope = 'Session'
      ShortCutStr = 'Shift+Ctrl+C'
    end
    object RulesAction: TUiAction
      Category = 'Session'
      Hint = 'Rules|Edits current Rules definitions.'
      ImageIndex = imgRules
      ShortCaption = 'Rules'
    end
    object SwapAction: TUiAction
      Category = 'Session'
      Caption = 'Swap Si&des'
      Hint = 'Swap Sides|Exchanges left, right files.'
      ImageIndex = imgSwap
      ShortCaption = 'Swap'
    end
    object ReportAction: TUiAction
      Category = 'Session'
      Caption = '%s Re&port...'
      Hint = '%0:s Report|Produces %0:s report.'
      ImageIndex = imgReport
      MacShortCutStr = 'Meta+P'
      ShortCaption = 'Report'
      ToolbarAllowed = False
    end
    object InfoAction: TUiAction
      Category = 'Session'
      Caption = '%s &Info'
      Hint = '%0:s Info|Displays %0:s statistics.'
      ImageIndex = imgInfo
      ShortCaption = 'Info'
      ShortCutStr = 'Ctrl+I'
      ToolbarAllowed = False
    end
    object CompareParentsAction: TUiAction
      Category = 'Session'
      Caption = 'Compare Parent &Folders'
      Hint = 'Compare Parent Folders|Compares folders containing current items in new view.'
      Scope = 'Session'
    end
    object MergeParentsAction: TUiAction
      Category = 'Session'
      Caption = 'Merge Parent &Folders'
      Hint = 'Merge Parent Folders|Merges folders containing current items in new view.'
      Scope = 'Session'
    end
    object InsigIgnoredAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Ignore &Unimportant Differences'
      Hint = 'Ignore Unimportant Differences|Treats unimportant differences as same.'
      ImageIndex = imgInsigIgnored
      ShortCaption = 'Minor'
    end
    object SameModIgnoredAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Ignore S&ame Changes'
      Hint = 'Ignore Same Changes|Treats same changes as same.'
      ShortCaption = 'Same OK'
    end
    object ShowToolbarAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Toolbar'
      Hint = 'Toolbar|Shows or hides toolbar.'
      Scope = 'Session'
    end
  end
  object Tree: TUiActionTree
    Nodes = ('Session: Menu', ('Settings: SeparatorItem', 'SessionSave: MenuItem', 'SessionSaveAs: MenuItem', 'SessionEdit: MenuItem', 'SessionLocked: MenuItem', 'SessionClear: MenuItem', 'CloseTab: MenuItem', 'Specs: SeparatorItem', 'Swap: MenuItem', 'Report: SeparatorItem', 'Report: MenuItem', 'Info: MenuItem', 'Views: SeparatorItem', 'CompareParents: MenuItem', 'MergeParents: MenuItem'), 'MergeFile: Menu', ('SessionEdit: MenuItem', 'Specs: SeparatorItem', 'Swap: MenuItem', 'Report: SeparatorItem', 'Report: MenuItem', 'Info: MenuItem', 'Last: SeparatorItem'), 'View: Menu', ('InsigIgnored: MenuItem', 'SameModIgnored: MenuItem', 'Layout: SeparatorItem', 'ShowToolbar: MenuItem'), 'Main: Toolbar', ('SessionHome: ToolButton', 'SessionsCombo: TreeButton', 'SessionSave: ToolButton', 'SessionSaveAs: ToolButton', 'SessionLocked: ToolButton', 'InsigIgnored: SeparatorButton', 'InsigIgnored: ToolButton', 'SameModIgnored: ToolButton', 'Rules: SeparatorButton', 'Rules: ToolButton', 'Specs: SeparatorButton', 'Swap: ToolButton', 'Report: ToolButton', 'Info: ToolButton'))
  end
end
