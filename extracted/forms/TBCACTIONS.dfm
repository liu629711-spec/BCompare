object BcActions: TBcActions
  OnCreate = DataModuleCreate
  OnDestroy = DataModuleDestroy
  object List: TUiActionList
    object MacCommandLineToolsAction: TUiAction
      Category = 'Mac'
      Caption = 'Install Command Line Tools...'
      Hint = 'Install Command Line Tools|Places bcomp and bcompare in /usr/local/bin/ folder to make BCompare available from the terminal prompt.'
      OnExecute = MacCommandLineToolsExecute
      Scope = 'Bc'
    end
    object SessionNewListAction: TUiAction
      Category = 'Session'
      Caption = '&New Session'
      Hint = 'New Session|Opens empty session of picked type in new view.'
      Scope = 'Bc'
    end
    object TabNewAction: TUiAction
      Category = 'Session'
      Caption = 'New &Tab'
      Hint = 'New Tab|Opens Home view in new tab.'
      OnExecute = TabNewExecute
      MacShortCutStr = 'Meta+T'
      Scope = 'Bc'
      ShortCutStr = 'Ctrl+T'
    end
    object WindowNewAction: TUiAction
      Category = 'Session'
      Caption = 'New &Window'
      Hint = 'New Window|Opens Home view in new window.'
      OnExecute = WindowNewExecute
      MacShortCutStr = 'Meta+N'
      Scope = 'Bc'
    end
    object SessionOpenAction: TUiAction
      Category = 'Session'
      Caption = '&Open Session'
      Hint = 'Open Session|Opens Home in new view.'
      OnExecute = SessionOpenExecute
      MacShortCutStr = 'Ctrl+Meta+O'
      Scope = 'Bc'
      ShortCutStr = 'Shift+Ctrl+O'
    end
    object WorkspaceLoadListAction: TUiAction
      Category = 'Session'
      Caption = 'Load Wor&kspace'
      Hint = 'Load Workspace|Restores picked saved view configuration.'
      OnExecute = WorkspaceLoadListExecute
      DynVisible = True
      Scope = 'Bc'
    end
    object WorkspaceManagerAction: TUiAction
      Category = 'Session'
      Caption = 'Manage Workspaces...'
      Hint = 'Manage Workspaces|Manages the saved view configurations that can be restored.'
      OnExecute = WorkspaceManagerExecute
      Scope = 'Bc'
    end
    object WorkspaceSaveAsAction: TUiAction
      Category = 'Session'
      Caption = 'Sa&ve Workspace As...'
      Hint = 'Save Workspace As|Stores current view configuration.'
      OnExecute = WorkspaceSaveAsExecute
      Scope = 'Bc'
    end
    object CloseTabAction: TUiAction
      Category = 'Session'
      Caption = 'Close Tab'
      Hint = 'Close Tab|Closes active tab.'
      OnExecute = CloseTabExecute
      MacShortCutStr = 'Meta+W'
      Scope = 'Bc'
      SecondaryShortCutStr = 'Ctrl+F4'
      ShortCutStr = 'Ctrl+W'
    end
    object ExitAction: TUiAction
      Category = 'Session'
      Caption = 'E&xit'
      Hint = 'Exit|Quits the application, prompts to save edits.'
      OnExecute = ExitExecute
      Scope = 'Bc'
      ShortCutStr = 'Ctrl+Q'
    end
    object UndoAction: TUiAction
      Category = 'Edit'
      Hint = 'Undo|Undoes previous action.'
      ImageIndex = imgUndo
      MacShortCutStr = 'Meta+Z'
      SecondaryShortCutStr = 'Alt+BkSp'
      ShortCaption = 'Undo'
      ShortCutStr = 'Ctrl+Z'
      ToolbarAllowed = False
    end
    object RedoAction: TUiAction
      Category = 'Edit'
      Hint = 'Redo|Redoes previously undone action.'
      ImageIndex = imgRedo
      MacShortCutStr = 'Shift+Meta+Z'
      SecondaryShortCutStr = 'Shift+Ctrl+Z,Shift+Alt+BkSp'
      ShortCaption = 'Redo'
      ShortCutStr = 'Ctrl+Y'
      ToolbarAllowed = False
    end
    object CutAction: TUiAction
      Category = 'Edit'
      Caption = 'Cu&t'
      Hint = 'Cut|Cuts selection and puts it on Clipboard.'
      ImageIndex = imgCut
      MacShortCutStr = 'Meta+X'
      SecondaryShortCutStr = 'Shift+Del'
      ShortCaption = 'Cut'
      ShortCutStr = 'Ctrl+X'
      ToolbarAllowed = False
    end
    object CopyAction: TUiAction
      Category = 'Edit'
      Caption = '&Copy'
      Hint = 'Copy|Copies selection and puts it on Clipboard.'
      ImageIndex = imgCopy
      MacShortCutStr = 'Meta+C'
      SecondaryShortCutStr = 'Ctrl+Ins'
      ShortCaption = 'Copy'
      ShortCutStr = 'Ctrl+C'
      ToolbarAllowed = False
    end
    object PasteAction: TUiAction
      Category = 'Edit'
      Caption = '&Paste'
      Hint = 'Paste|Inserts Clipboard contents.'
      ImageIndex = imgPaste
      MacShortCutStr = 'Meta+V'
      SecondaryShortCutStr = 'Shift+Ins'
      ShortCaption = 'Paste'
      ShortCutStr = 'Ctrl+V'
      ToolbarAllowed = False
    end
    object SelectAllAction: TUiAction
      Category = 'Edit'
      Caption = 'Select &All'
      Hint = 'Select All|Selects all visible items.'
      MacShortCutStr = 'Meta+A'
      ShortCutStr = 'Ctrl+A'
    end
    object ProgramOptionsAction: TUiAction
      Category = 'Tools'
      Caption = '&Options...'
      Hint = 'Options|Sets global preferences.'
      ImageIndex = imgOptions
      OnExecute = ProgramOptionsExecute
      MacShortCutStr = 'Meta+,'
      Scope = 'Bc'
      ShortCaption = 'Options'
      ToolbarAllowed = False
    end
    object FileFormatManagerAction: TUiAction
      Category = 'Tools'
      Caption = 'File &Formats...'
      Hint = 'File Formats|Manages file formats.'
      ImageIndex = imgFileFormatManager
      OnExecute = FileFormatManagerExecute
      Scope = 'Bc'
      ShortCaption = 'File Formats'
      ToolbarAllowed = False
    end
    object ProfileManagerAction: TUiAction
      Category = 'Tools'
      Caption = '&Profiles...'
      Hint = 'Profiles|Manages profiles.'
      OnExecute = ProfileManagerExecute
      Scope = 'Bc'
    end
    object SourceControlManagerAction: TUiAction
      Category = 'Tools'
      Caption = 'Source Co&ntrol Integration...'
      Hint = 'Source Control Integration|Manages integration with version control systems.'
      OnExecute = SourceControlManagerExecute
      MenuAllowed = False
      Scope = 'Bc'
    end
    object ExportAction: TUiAction
      Category = 'Tools'
      Caption = '&Export Settings...'
      Hint = 'Export Settings|Saves user settings as a file.'
      OnExecute = ExportExecute
      Scope = 'Bc'
    end
    object ImportAction: TUiAction
      Category = 'Tools'
      Caption = '&Import Settings...'
      Hint = 'Import Settings|Loads user settings from a file.'
      OnExecute = ImportExecute
      Scope = 'Bc'
    end
    object RestoreAction: TUiAction
      Category = 'Tools'
      Caption = '&Restore Factory Defaults...'
      Hint = 'Restore Factory Defaults|Loads factory default settings.'
      OnExecute = RestoreExecute
      Scope = 'Bc'
    end
    object SaveSnapshotAction: TUiAction
      Category = 'Tools'
      Caption = 'Save Snaps&hot...'
      Hint = 'Save Snapshot|Saves details of specified folder for future comparison.'
      ImageIndex = imgSaveSnapshot
      OnExecute = SaveSnapshotExecute
      Scope = 'Bc'
      ShortCaption = 'Snapshot'
      ToolbarAllowed = False
    end
    object EditTextFileAction: TUiAction
      Category = 'Tools'
      Caption = 'E&dit Text File'
      Hint = 'Edit Text File|Opens new Text Edit view.'
      ImageIndex = imgTextEditSession
      OnExecute = EditTextFileExecute
      Scope = 'Bc'
      ShortCaption = 'Text Edit'
      ToolbarAllowed = False
    end
    object ViewPatchAction: TUiAction
      Category = 'Tools'
      Caption = 'View P&atch...'
      Hint = 'View Patch|Opens picked patch file in new Text Patch view.'
      ImageIndex = imgTextPatchSession
      OnExecute = ViewPatchExecute
      Scope = 'Bc'
      ShortCaption = 'Patch'
      ToolbarAllowed = False
    end
    object DebugListAction: TUiAction
      Category = 'Tools'
      Scope = 'Bc'
    end
    object DebugIdentifyControlAction: TUiAction
      Category = 'Tools'
      OnExecute = DebugIdentifyControlExecute
      Scope = 'Bc'
    end
    object DebugRaiseExceptionAction: TUiAction
      Category = 'Tools'
      OnExecute = DebugRaiseExceptionExecute
      Scope = 'Bc'
    end
    object MacWindowMinimizeAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Minimize'
      Hint = 'Minimize|Minimizes active window.'
      OnExecute = MacWindowMinimizeExecute
      MacDynGroup = True
      MacShortCutStr = 'Meta+M'
      Scope = 'Bc'
    end
    object MacWindowMinimizeAllAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Minimize All'
      Hint = 'Minimize All|Minimizes all application windows.'
      OnExecute = MacWindowMinimizeAllExecute
      MacDynGroup = True
      MacShortCutStr = 'Alt+Meta+M'
      Scope = 'Bc'
    end
    object MacWindowZoomAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Zoom'
      Hint = 'Zoom|Maximizes or restores active window.'
      OnExecute = MacWindowZoomExecute
      MacDynGroup = True
      Scope = 'Bc'
    end
    object MacWindowZoomAllAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Zoom All'
      Hint = 'Zoom All|Maximizes all visible document windows.'
      OnExecute = MacWindowZoomAllExecute
      MacDynGroup = True
      MacDynShiftState = [ssAlt]
      Scope = 'Bc'
    end
    object MacWindowNextAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Cycle Through Windows'
      Hint = 'Cycle Through Windows|Selects window after active one.'
      OnExecute = MacWindowNextExecute
      MacShortCutStr = 'Meta+`'
      Scope = 'Bc'
    end
    object MacWindowPrevAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Cycle Back Through Windows'
      Hint = 'Cycle Back Through Windows|Selects window before active one.'
      OnExecute = MacWindowPrevExecute
      MacShortCutStr = 'Shift+Meta+`'
      MenuAllowed = False
      Scope = 'Bc'
    end
    object TabNextAction: TUiAction
      Category = 'MacWindow'
      Hint = 'Select Next Tab|Selects tab after active one.'
      OnExecute = TabNextExecute
      MacShortCutStr = 'Shift+Meta+]'
      Scope = 'Bc'
      ShortCutStr = 'Ctrl+Tab'
    end
    object TabPrevAction: TUiAction
      Category = 'MacWindow'
      Hint = 'Select Previous Tab|Selects tab before active one.'
      OnExecute = TabPrevExecute
      MacShortCutStr = 'Shift+Meta+['
      Scope = 'Bc'
      ShortCutStr = 'Shift+Ctrl+Tab'
    end
    object MacTabToWindowAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Move Tab to New Window'
      Hint = 'Move Tab to New Window|Removes active tab and makes it into new window.'
      OnExecute = MacTabToWindowExecute
      Scope = 'Bc'
    end
    object MacWindowMergeAllAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Merge All Windows'
      Hint = 'Merge All Windows|Moves all tabs onto active window.'
      OnExecute = MacWindowMergeAllExecute
      Scope = 'Bc'
    end
    object MacWindowActivateAllAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Bring All to Front'
      Hint = 'Bring All to Front|Brings all windows to the foreground.'
      OnExecute = MacWindowActivateAllExecute
      MacDynGroup = True
      Scope = 'Bc'
    end
    object MacWindowArrangeAllAction: TUiAction
      Category = 'MacWindow'
      Caption = 'Arrange in Front'
      Hint = 'Arrange in Front|Arranges all visible windows.'
      OnExecute = MacWindowArrangeAllExecute
      MacDynGroup = True
      MacDynShiftState = [ssAlt]
      Scope = 'Bc'
    end
    object HelpContentsAction: TUiAction
      Category = 'Help'
      Caption = '&Contents'
      Hint = 'Contents|Shows help file.'
      ImageIndex = imgHelpContents
      OnExecute = HelpContentsExecute
      Scope = 'Bc'
      ShortCaption = 'Help'
      ToolbarAllowed = False
    end
    object ContextHelpAction: TUiAction
      Category = 'Help'
      Caption = 'Context Sensitive &Help'
      Hint = 'Context Sensitive Help|Shows context sensitive help for the active window.'
      OnExecute = ContextHelpExecute
      Scope = 'Bc'
      ShortCutStr = 'F1'
    end
    object VisitSiteAction: TUiAction
      Category = 'Help'
      Caption = 'Scooter Software on the &Web'
      Hint = 'Scooter Software on the Web|Opens the Scooter Software website in your browser.'
      OnExecute = VisitSiteExecute
      Scope = 'Bc'
    end
    object CheckForUpdatesAction: TUiAction
      Category = 'Help'
      Caption = 'Check for &Updates'
      Hint = 'Check for Updates|Checks our website to see if a newer version is available.'
      OnExecute = CheckForUpdatesExecute
      Scope = 'Bc'
    end
    object SupportAction: TUiAction
      Category = 'Help'
      Caption = '&Support'
      Hint = 'Support|Displays Scooter Software contact information.'
      OnExecute = SupportExecute
      Scope = 'Bc'
    end
    object EnterKeyAction: TUiAction
      Category = 'Help'
      Caption = '&Enter Key...'
      Hint = 'Enter Key|Enter registration key.'
      OnExecute = EnterKeyExecute
      Scope = 'Bc'
    end
    object AboutAction: TUiAction
      Category = 'Help'
      Caption = '&About %s'
      Hint = 'About %s|Displays program information, version number and copyright.'
      OnExecute = AboutExecute
      Scope = 'Bc'
    end
  end
  object Tree: TUiActionTree
    Nodes = ('Mac: Menu', ('About: MenuItem', 'N1: SeparatorItem', 'ProgramOptions: MenuItem', 'FileFormatManager: MenuItem', 'ProfileManager: MenuItem', 'N2: SeparatorItem', 'CheckForUpdates: MenuItem', 'EnterKey: MenuItem', 'MacCommandLineTools: MenuItem', 'N3: SeparatorItem'), 'Session: Menu', ('SessionNewList: SubmenuItem', ('DirCompareNew: MenuItem', 'DirMergeNew: MenuItem', 'DirSyncNew: MenuItem', 'TextCompareNew: MenuItem', 'TextMergeNew: MenuItem', 'HexCompareNew: MenuItem', 'MediaCompareNew: MenuItem', 'PixCompareNew: MenuItem', 'RegCompareNew: MenuItem', 'TableCompareNew: MenuItem', 'VerCompareNew: MenuItem', 'XMLCompareNew: MenuItem'), 'TabNew: MenuItem', 'WindowNew: MenuItem', 'SessionOpen: MenuItem', 'Workspace: SeparatorItem', 'WorkspaceLoadList: SubmenuItem', ('N1: SeparatorItem', 'WorkspaceManager: MenuItem'), 'WorkspaceSaveAs: MenuItem', 'Settings: SeparatorItem', 'CloseTab: MenuItem', 'Last: SeparatorItem', 'Exit: MenuItem'), 'MergeFile: Menu', ('Exit: MenuItem'), 'Edit: Menu', ('Undo: MenuItem', 'Redo: MenuItem', 'Common: SeparatorItem', 'Cut: MenuItem', 'Copy: MenuItem', 'Paste: MenuItem', 'Select: SeparatorItem', 'SelectAll: MenuItem'), 'View: Menu', (), 'Tools: Menu', ('ProgramOptions: MenuItem', 'FileFormatManager: MenuItem', 'ProfileManager: MenuItem', 'SourceControlManager: MenuItem', 'N1: SeparatorItem', 'Export: MenuItem', 'Import: MenuItem', 'Restore: MenuItem', 'N2: SeparatorItem', 'SaveSnapshot: MenuItem', 'EditTextFile: MenuItem', 'ViewPatch: MenuItem', 'N3: SeparatorItem', 'DebugList: SubmenuItem', ('DebugIdentifyControl: MenuItem', 'DebugRaiseException: MenuItem')), 'MacTools: Menu', ('Export: MenuItem', 'Import: MenuItem', 'Restore: MenuItem', 'N1: SeparatorItem', 'SaveSnapshot: MenuItem', 'EditTextFile: MenuItem', 'ViewPatch: MenuItem', 'N2: SeparatorItem', 'DebugList: SubmenuItem', ('DebugIdentifyControl: MenuItem', 'DebugRaiseException: MenuItem')), 'MacWindow: Menu', ('MacWindowMinimize: MenuItem', 'MacWindowMinimizeAll: MenuItem', 'MacWindowZoom: MenuItem', 'MacWindowZoomAll: MenuItem', 'MacWindowNext: MenuItem', 'MacWindowPrev: MenuItem', 'N1: SeparatorItem', 'TabNext: MenuItem', 'TabPrev: MenuItem', 'MacTabToWindow: MenuItem', 'MacWindowMergeAll: MenuItem', 'N2: SeparatorItem', 'MacWindowActivateAll: MenuItem', 'MacWindowArrangeAll: MenuItem', 'N3: SeparatorItem'), 'MacHelp: Menu', ('HelpContents: MenuItem', 'N1: SeparatorItem', 'VisitSite: MenuItem', 'Support: MenuItem'), 'Help: Menu', ('HelpContents: MenuItem', 'ContextHelp: MenuItem', 'N1: SeparatorItem', 'VisitSite: MenuItem', 'CheckForUpdates: MenuItem', 'Support: MenuItem', 'EnterKey: MenuItem', 'N2: SeparatorItem', 'About: MenuItem'), 'Main: Toolbar', ('Tools: SeparatorButton', 'ProgramOptions: ToolButton', 'FileFormatManager: ToolButton', 'SaveSnapshot: ToolButton', 'EditTextFile: ToolButton', 'ViewPatch: ToolButton', 'Help: SeparatorButton', 'HelpContents: ToolButton'))
  end
end
