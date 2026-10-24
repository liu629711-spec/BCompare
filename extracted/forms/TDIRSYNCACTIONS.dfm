object DirSyncActions: TDirSyncActions
  object List: TUiActionList
    object RunAction: TUiAction
      Category = 'Session'
      Hint = 'Run Sync|Performs all sync operations.'
      ImageIndex = imgSyncRun
    end
    object CompareBaseViewAction: TUiAction
      Category = 'Session'
      Caption = 'Co&mpare Base Folders'
      Hint = 'Compare Base Folders|Compares base folders in new view.'
      ImageIndex = imgDirCompareSession
      ShortCaption = 'Compare View'
      ToolbarAllowed = False
    end
    object SyncLeaveAction: TUiAction
      Category = 'Actions'
      Caption = 'Lea&ve Alone'
      Hint = 'Leave Alone|Changes sync operation to leave alone.'
    end
    object SyncCopyLeftAction: TUiAction
      Category = 'Actions'
      Caption = 'Copy Right to &Left'
      Hint = 'Copy Right to Left|Changes sync operation to copy right to left.'
      ImageIndex = imgCopyLeft
    end
    object SyncCopyRightAction: TUiAction
      Category = 'Actions'
      Caption = 'Copy Left to &Right'
      Hint = 'Copy Left to Right|Changes sync operation to copy left to right.'
      ImageIndex = imgCopyRight
    end
    object SyncDeleteLeftAction: TUiAction
      Category = 'Actions'
      Caption = 'Delete Le&ft'
      Hint = 'Delete Left|Changes sync operation to delete left.'
      ImageIndex = imgDelete
    end
    object SyncDeleteRightAction: TUiAction
      Category = 'Actions'
      Caption = 'Delete Ri&ght'
      Hint = 'Delete Right|Changes sync operation to delete right.'
      ImageIndex = imgDelete
    end
    object ConflictNextAction: TUiAction
      Category = 'Search'
      Caption = '&Next Conflict'
      Hint = 'Next Conflict|Positions at next conflict.'
      ImageIndex = imgDown
      MacShortCutStr = 'Ctrl+Alt+Down'
      ShortCaption = 'Next Conflict'
      ShortCutStr = 'Ctrl+N'
      ToolbarAllowed = False
    end
    object ConflictPrevAction: TUiAction
      Category = 'Search'
      Caption = '&Previous Conflict'
      Hint = 'Previous Conflict|Positions at previous conflict.'
      ImageIndex = imgUp
      MacShortCutStr = 'Ctrl+Alt+Up'
      ShortCaption = 'Prev Conflict'
      ShortCutStr = 'Ctrl+P'
      ToolbarAllowed = False
    end
  end
  object Tree: TUiActionTree
    Nodes = ('Session: Menu', ('Info: MenuItem', 'Run: MenuItem', 'Views: SeparatorItem', 'CompareBaseView: MenuItem'), 'Actions: Menu', ('SyncLeave: MenuItem', 'SyncCopyLeft: MenuItem', 'SyncCopyRight: MenuItem', 'SyncDeleteLeft: MenuItem', 'SyncDeleteRight: MenuItem', 'N1: SeparatorItem'), 'Search: Menu', ('ConflictNext: MenuItem', 'ConflictPrev: MenuItem'), 'Main: Toolbar', ('Search: SeparatorButton', 'ConflictNext: ToolButton', 'ConflictPrev: ToolButton', 'Info: ToolButton', 'CompareBaseView: ToolButton'), 'Tree: PopupMenu', ('SyncLeave: MenuItem', 'SyncCopyLeft: MenuItem', 'SyncCopyRight: MenuItem', 'SyncDeleteLeft: MenuItem', 'SyncDeleteRight: MenuItem', 'First: SeparatorItem'))
  end
end
