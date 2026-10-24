object TextActions: TTextActions
  object List: TUiActionList
    object SelectAllAction: TUiAction
      Hint = 'Select All|Selects all visible lines.'
    end
    object FileFormatAction: TUiAction
      ImageIndex = imgTextFormatEdit
    end
    object ExistsNextAction: TUiAction
      Hint = 'Next Existing Line|Positions at next existing line, skipping over gaps.'
    end
    object ExistsPrevAction: TUiAction
      Hint = 'Previous Existing Line|Positions at previous existing line, skipping over gaps.'
    end
    object FavCompareAllAction: TUiAction
      Hint = 'Show All|Shows same, left orphan, right orphan and difference lines.'
    end
    object FavDiffAction: TUiAction
      Hint = 'Show Differences|Shows left orphan, right orphan and difference lines.'
    end
    object FavSameAction: TUiAction
      Hint = 'Show Same|Shows same lines.'
    end
    object FavCompareNoneAction: TUiAction
      Hint = 'Show None|Shows no lines.'
    end
    object TogSameAction: TUiAction
      Hint = 'Toggle Same|Shows or hides same lines.'
    end
    object TogLeftOrphanAction: TUiAction
      Hint = 'Toggle Left Orphans|Shows or hides left orphan lines.'
    end
    object TogRightOrphanAction: TUiAction
      Hint = 'Toggle Right Orphans|Shows or hides right orphan lines.'
    end
    object TogDiffAction: TUiAction
      Hint = 'Toggle Differences|Shows or hides difference lines.'
    end
    object CheckInAction: TUiAction
      Category = 'File'
      Caption = 'Check &In...'
      Hint = 'Check In|Checks file into source control.'
    end
    object CheckOutAction: TUiAction
      Category = 'File'
      Caption = 'Check Ou&t'
      Hint = 'Check Out|Checks out file from source control.'
    end
    object UndoCheckOutAction: TUiAction
      Category = 'File'
      Caption = '&Undo Check Out'
      Hint = 'Undo Check Out|Undoes checkout from source control.'
    end
    object ApplyPatchAction: TUiAction
      Category = 'File'
      Caption = '&Apply Patch'
      Hint = 'Apply Patch|Applies patch file.'
    end
    object AlignWithAction: TUiAction
      Category = 'Edit'
      Caption = 'Align &With...'
      Hint = 'Align With|Marks selected lines for manual realignment.'
      MacShortCutStr = 'Shift+Meta+A'
      ShortCutStr = 'F7'
    end
    object IsolateAction: TUiAction
      Category = 'Edit'
      Caption = 'I&solate'
      Hint = 'Isolate|Realigns comparison so that selected lines are by themselves.'
    end
    object ReplacementAction: TUiAction
      Category = 'Edit'
      Caption = 'Replace&ment...'
      Hint = 'Replacement|Adds item to replacement list based on current difference.'
    end
    object CopyRightAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y to Right'
      Hint = 'Copy to Right|Copies selected lines or current section to right pane.'
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
      Hint = 'Copy to Left|Copies selected lines or current section to left pane.'
      ImageIndex = imgCopyLeft
      MacShortCutStr = 'Alt+Meta+Left'
      MenuAllowed = False
      ShortCaption = 'Copy'
      ShortCutStr = 'Ctrl+L'
      ToolbarAllowed = False
    end
    object CopySideAction: TUiAction
      Category = 'Edit'
      Hint = 'Copy to Other Side|Copies selected lines or current section to pane on other side.'
    end
    object CopyItemRightAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y Line to Right'
      Hint = 'Copy Line to Right|Copies current line to right pane.'
      MacShortCutStr = 'Ctrl+Meta+Right'
      MenuAllowed = False
      ShortCaption = 'Copy Line'
      ShortCutStr = 'Shift+Ctrl+R'
      ToolbarAllowed = False
    end
    object CopyItemLeftAction: TUiAction
      Category = 'Edit'
      Caption = 'Cop&y Line to Left'
      Hint = 'Copy Line to Left|Copies current line to left pane.'
      MacShortCutStr = 'Ctrl+Meta+Left'
      MenuAllowed = False
      ShortCaption = 'Copy Line'
      ShortCutStr = 'Shift+Ctrl+L'
      ToolbarAllowed = False
    end
    object CopyItemSideAction: TUiAction
      Category = 'Edit'
      Hint = 'Copy Line to Other Side|Copies current line to pane on other side.'
      ToolbarAllowed = False
    end
    object ConflictAction: TUiAction
      Category = 'Edit'
      AutoCheck = True
      Caption = '&Conflict'
      Hint = 'Conflict|Clears or sets conflict for selected lines or current section.'
      ImageIndex = imgConflict
      ShortCaption = 'Conflict'
    end
    object TakeLeftAction: TUiAction
      Category = 'Edit'
      Caption = 'Ta&ke Left'
      Hint = 'Take Left|Takes selected lines or current section from left pane.'
      MacShortCutStr = 'Alt+Meta+Left'
      ShortCaption = 'Left'
      ShortCutStr = 'Ctrl+L'
    end
    object TakeCenterAction: TUiAction
      Category = 'Edit'
      Caption = 'Ta&ke Center'
      Hint = 'Take Center|Takes selected lines or current section from center pane.'
      ShortCaption = 'Center'
    end
    object TakeRightAction: TUiAction
      Category = 'Edit'
      Caption = 'Ta&ke Right'
      Hint = 'Take Right|Takes selected lines or current section from right pane.'
      MacShortCutStr = 'Alt+Meta+Right'
      ShortCaption = 'Right'
      ShortCutStr = 'Ctrl+R'
    end
    object TakeLeftRightAction: TUiAction
      Category = 'Edit'
      Caption = 'Take Left Then Ri&ght'
      Hint = 'Take Left Then Right|Takes selected lines or current section from left then right panes.'
      MacShortCutStr = 'Meta+B'
      ShortCutStr = 'Ctrl+B'
    end
    object TakeRightLeftAction: TUiAction
      Category = 'Edit'
      Caption = 'Take Rig&ht Then Left'
      Hint = 'Take Right Then Left|Takes selected lines or current section from right then left panes.'
      MacShortCutStr = 'Shift+Meta+B'
      ShortCutStr = 'Shift+Ctrl+B'
    end
    object TakeItemLeftAction: TUiAction
      Category = 'Edit'
      Caption = 'Ta&ke Left Line'
      Hint = 'Take Left Line|Takes current line from left pane.'
      MacShortCutStr = 'Ctrl+Meta+Left'
      ShortCutStr = 'Shift+Ctrl+L'
    end
    object TakeItemCenterAction: TUiAction
      Category = 'Edit'
      Caption = 'Ta&ke Center Line'
      Hint = 'Take Center Line|Takes current line from center pane.'
    end
    object TakeItemRightAction: TUiAction
      Category = 'Edit'
      Caption = 'Ta&ke Right Line'
      Hint = 'Take Right Line|Takes current line from right pane.'
      MacShortCutStr = 'Ctrl+Meta+Right'
      ShortCutStr = 'Shift+Ctrl+R'
    end
    object IncreaseIndentAction: TUiAction
      Category = 'Edit'
      Caption = 'I&ncrease Indent'
      Hint = 'Increase Indent|Increases indentation of selected lines.'
      MacShortCutStr = 'Meta+]'
      ShortCutStr = 'Shift+Ctrl+I'
    end
    object DecreaseIndentAction: TUiAction
      Category = 'Edit'
      Caption = 'D&ecrease Indent'
      Hint = 'Decrease Indent|Decreases indentation of selected lines.'
      MacShortCutStr = 'Meta+['
      ShortCutStr = 'Shift+Ctrl+U'
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
      Caption = '&Delete Line'
      Hint = 'Delete Line|Deletes current line.'
      MenuAllowed = False
    end
    object DeleteItemBeginAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete to Start of Line'
      Hint = 'Delete to Start of Line|Deletes to start of current line.'
      MacShortCutStr = 'Meta+BkSp'
      MenuAllowed = False
      ShortCutStr = 'Shift+Ctrl+BkSp'
    end
    object DeleteItemEndAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete to End of Line'
      Hint = 'Delete to End of Line|Deletes to end of current line.'
      MacShortCutStr = 'Ctrl+K'
      MenuAllowed = False
      ShortCutStr = 'Shift+Ctrl+Del'
    end
    object DeleteWordAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete Word'
      Hint = 'Delete Word|Deletes current word.'
      MenuAllowed = False
    end
    object DeleteWordBeginAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete to Start of Word'
      Hint = 'Delete to Start of Word|Deletes to start of current word.'
      MacShortCutStr = 'Alt+BkSp'
      MenuAllowed = False
      ShortCutStr = 'Ctrl+BkSp'
    end
    object DeleteWordEndAction: TUiAction
      Category = 'Edit'
      Caption = '&Delete to End of Word'
      Hint = 'Delete to End of Word|Deletes to end of current word.'
      MacShortCutStr = 'Alt+Del'
      MenuAllowed = False
      ShortCutStr = 'Ctrl+Del'
    end
    object InsertItemBeforeAction: TUiAction
      Category = 'Edit'
      Caption = 'Insert Line &Before'
      Hint = 'Insert Line Before|Inserts new line before current one.'
      MacShortCutStr = 'Shift+Ctrl+Enter'
      MenuAllowed = False
      ShortCutStr = 'Shift+Ctrl+Enter'
    end
    object InsertItemAfterAction: TUiAction
      Category = 'Edit'
      Caption = '&Insert Line After'
      Hint = 'Insert Line After|Inserts new line after current one.'
      MacShortCutStr = 'Ctrl+Enter'
      MenuAllowed = False
      ShortCutStr = 'Ctrl+Enter'
    end
    object SelectSectionAction: TUiAction
      Category = 'Edit'
      Caption = 'Select Secti&on'
      Hint = 'Select Section|Selects all lines in current section.'
      MacShortCutStr = 'Meta+D'
      ShortCutStr = 'Ctrl+D'
    end
    object CompareToClipboardAction: TUiAction
      Category = 'Edit'
      Caption = 'Compare Se&lection to Clipboard'
      Hint = 'Compare Selection to Clipboard|Compares selected text to clipboard in new view.'
    end
    object ConvertListAction: TUiAction
      Category = 'Edit'
      Caption = 'Con&vert File'
      Hint = 'Convert File|Performs picked file conversion.'
    end
    object TrimTrailWSAction: TUiAction
      Category = 'Edit'
      Caption = 'Trim &Trailing Whitespace'
      Hint = 'Trim Trailing Whitespace|Strips off spaces and tab characters at the end of lines.'
    end
    object LeadSpaceToTabAction: TUiAction
      Category = 'Edit'
      Caption = '&Leading Spaces to Tabs'
      Hint = 'Leading Spaces to Tabs|Replaces spaces at the beginning of lines with tab characters.'
    end
    object TabToSpaceAction: TUiAction
      Category = 'Edit'
      Caption = 'Tabs to &Spaces'
      Hint = 'Tabs to Spaces|Replaces tab characters with spaces.'
    end
    object EndingStyleListAction: TUiAction
      Category = 'Edit'
      Caption = 'Line &Endings'
      Hint = 'Line Endings|Converts line endings to picked style.'
    end
    object ToWindowsAction: TUiAction
      Category = 'Edit'
      Caption = 'To &Windows/DOS'
      Hint = 'To Windows/DOS|Converts line endings to Windows/DOS style.'
    end
    object ToUnixAction: TUiAction
      Category = 'Edit'
      Caption = 'To &Unix'
      Hint = 'To Unix|Converts line endings to Unix style.'
    end
    object ToMacAction: TUiAction
      Category = 'Edit'
      Caption = 'To &Macintosh'
      Hint = 'To Macintosh|Converts line endings to Macintosh style.'
    end
    object ConflictSectionOffNextAction: TUiAction
      Category = 'Search'
      Caption = 'Clear &Conflict Section, Next'
      Hint = 'Clear Conflict Section, Next|Clears conflict for current section and positions at next conflict section.'
      ImageIndex = imgConflictSectionOffNext
      ShortCaption = 'Clear Conflict, Next'
      ToolbarAllowed = False
    end
    object ConflictSectionNextAction: TUiAction
      Category = 'Search'
      Caption = 'Next &Conflict Section'
      Hint = 'Next Conflict Section|Positions at next conflict section.'
      ImageIndex = imgConflictSectionNext
      MacShortCutStr = 'Shift+Alt+Down'
      ShortCaption = 'Next Conflict'
      ShortCutStr = 'Alt+N'
    end
    object ConflictSectionPrevAction: TUiAction
      Category = 'Search'
      Caption = 'Previous &Conflict Section'
      Hint = 'Previous Conflict Section|Positions at previous conflict section.'
      ImageIndex = imgConflictSectionPrev
      MacShortCutStr = 'Shift+Alt+Up'
      ShortCaption = 'Prev Conflict'
      ShortCutStr = 'Alt+P'
    end
    object DiffNextAction: TUiAction
      Category = 'Search'
      Caption = 'Nex&t Difference'
      Hint = 'Next Difference|Positions at next difference text.'
      MacShortCutStr = 'Ctrl+Alt+Down'
      ShortCutStr = 'Shift+Ctrl+N'
    end
    object DiffPrevAction: TUiAction
      Category = 'Search'
      Caption = 'Previo&us Difference'
      Hint = 'Previous Difference|Positions at previous difference text.'
      MacShortCutStr = 'Ctrl+Alt+Up'
      ShortCutStr = 'Shift+Ctrl+P'
    end
    object DiffSectionNextAction: TUiAction
      Category = 'Search'
      Caption = '&Next Difference Section'
      Hint = 'Next Difference Section|Positions at next unignored difference section.'
      ImageIndex = imgDown
      MacShortCutStr = 'Alt+Down'
      ShortCaption = 'Next Section'
      ShortCutStr = 'Ctrl+N'
    end
    object DiffSectionPrevAction: TUiAction
      Category = 'Search'
      Caption = '&Previous Difference Section'
      Hint = 'Previous Difference Section|Positions at previous unignored difference section.'
      ImageIndex = imgUp
      MacShortCutStr = 'Alt+Up'
      ShortCaption = 'Prev Section'
      ShortCutStr = 'Ctrl+P'
    end
    object DiffReplacedNextAction: TUiAction
      Category = 'Search'
      Caption = 'Next Repl&acement'
      Hint = 'Next Replacement|Positions at next replacement text.'
      MacShortCutStr = 'Shift+Ctrl+Alt+Down'
      ShortCutStr = 'Shift+Ctrl+Alt+N'
    end
    object DiffReplacedPrevAction: TUiAction
      Category = 'Search'
      Caption = 'Previous Replace&ment'
      Hint = 'Previous Replacement|Positions at previous replacement text.'
      MacShortCutStr = 'Shift+Ctrl+Alt+Up'
      ShortCutStr = 'Shift+Ctrl+Alt+P'
    end
    object TakenLeftNextAction: TUiAction
      Category = 'Search'
      Caption = 'Next Left T&aken'
      Hint = 'Next Left Taken|Positions at next range of lines where left was taken.'
    end
    object TakenLeftPrevAction: TUiAction
      Category = 'Search'
      Caption = 'Previous Left T&aken'
      Hint = 'Previous Left Taken|Positions at previous range of lines where left was taken.'
    end
    object TakenRightNextAction: TUiAction
      Category = 'Search'
      Caption = 'Next Rig&ht Taken'
      Hint = 'Next Right Taken|Positions at next range of lines where right was taken.'
    end
    object TakenRightPrevAction: TUiAction
      Category = 'Search'
      Caption = 'Previous Rig&ht Taken'
      Hint = 'Previous Right Taken|Positions at previous range of lines where right was taken.'
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
    object FindInFilesAction: TUiAction
      Category = 'Search'
      Caption = 'Find in File&s...'
      Hint = 'Find in Files|Finds search string in multiple files.'
      ImageIndex = imgFindInFiles
      MacShortCutStr = 'Shift+Meta+F'
      ShortCaption = 'Files'
      ShortCutStr = 'Shift+Ctrl+F'
    end
    object MacFindUseSelAction: TUiAction
      Category = 'Search'
      Caption = 'Use Selection for Find'
      Hint = 'Use Selection for Find|Finds selected text.'
      MacShortCutStr = 'Meta+E'
    end
    object GoToAction: TUiAction
      Category = 'Search'
      Caption = '&Go To...'
      Hint = 'Go To|Positions at specified line and column.'
      ImageIndex = imgGoTo
      MacShortCutStr = 'Meta+L'
      ShortCaption = 'Go To'
      ShortCutStr = 'Ctrl+G'
      ToolbarAllowed = False
    end
    object BookmarkToggleListAction: TUiAction
      Category = 'Search'
      Caption = 'Toggle &Bookmark'
      Hint = 'Toggle Bookmark|Sets or clears picked bookmark.'
    end
    object BookmarkGoToListAction: TUiAction
      Category = 'Search'
      Caption = 'Go to Boo&kmark'
      Hint = 'Go to Bookmark|Positions at picked bookmark.'
    end
    object BookmarkClearAction: TUiAction
      Category = 'Search'
      Caption = 'C&lear Bookmarks'
      Hint = 'Clear Bookmarks|Removes all bookmarks.'
    end
    object GoInputAction: TUiAction
      Category = 'Search'
      Hint = 'Go Input|Positions in input pane.'
      MacShortCutStr = 'Alt+PgUp'
      ShortCutStr = 'Alt+PgUp'
    end
    object GoOutputAction: TUiAction
      Category = 'Search'
      Hint = 'Go Output|Positions in output pane.'
      MacShortCutStr = 'Alt+PgDn'
      ShortCutStr = 'Alt+PgDn'
    end
    object FavMergeAllAction: TUiAction
      Category = 'Favorites'
      Caption = 'Show All'
      Hint = 'Show All|Shows unchanged, same change, left change, right change, different change and conflict lines.'
      ImageIndex = imgFavAll
      ShortCaption = 'All'
    end
    object FavChangedAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Changes'
      Hint = 'Show Changes|Shows same change, left change, right change, different change and conflict lines.'
      ImageIndex = imgFavDiff
      ShortCaption = 'Diffs'
    end
    object FavConflictAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Conflicts'
      Hint = 'Show Conflicts|Shows conflict lines.'
      ShortCaption = 'Conflicts'
    end
    object FavLeftAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Left Changes'
      Hint = 'Show Left Changes|Shows same change, left change, different change and conflict lines.'
      ShortCaption = 'Left'
    end
    object FavRightAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Right Changes'
      Hint = 'Show Right Changes|Shows same change, right change, different change and conflict lines.'
      ShortCaption = 'Right'
    end
    object FavMergeableAction: TUiAction
      Category = 'DropDown'
      Caption = 'Show Mergeable'
      Hint = 'Show Mergeable|Shows same change, left change, right change and different change lines.'
      ShortCaption = 'Okay'
    end
    object FavUnchangedAction: TUiAction
      Category = 'Favorites'
      Caption = 'Show Unchanged'
      Hint = 'Show Unchanged|Shows unchanged lines.'
      ImageIndex = imgFavSame
      ShortCaption = 'Same'
    end
    object FavMergeNoneAction: TUiAction
      Category = 'View'
      Caption = 'Show None'
      Hint = 'Show None|Shows no lines.'
      ImageIndex = imgFavNone
      MenuAllowed = False
      ShortCaption = 'None'
      ToolbarAllowed = False
    end
    object TogNoModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Unchanged|Shows or hides unchanged lines.'
      ShortCaption = 'Same'
    end
    object TogSameModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Same Changes|Shows or hides same change lines.'
      ShortCaption = 'Same Diffs'
    end
    object TogLeftModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Left Changes|Shows or hides left change lines.'
      ShortCaption = 'Left'
    end
    object TogRightModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Right Changes|Shows or hides right change lines.'
      ShortCaption = 'Right'
    end
    object TogDiffModAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Different Changes|Shows or hides different change lines.'
      ShortCaption = 'Diffs'
    end
    object TogConflictAction: TUiAction
      Category = 'Toggles'
      Hint = 'Toggle Conflicts|Shows or hides conflict lines.'
      ShortCaption = 'Conflicts'
    end
    object ShowContextAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Show &Context'
      Hint = 'Show Context|Shows lines surrounding difference.'
      ImageIndex = imgShowContext
      ShortCaption = 'Context'
    end
    object FavorLeftAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Favor &Left Changes'
      Hint = 'Favor Left Changes|Suppresses highlighting of left-only changes in output.'
      ImageIndex = imgFavorLeft
      ShortCaption = 'Favor Left'
    end
    object FavorRightAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Fa&vor Right Changes'
      Hint = 'Favor Right Changes|Suppresses highlighting of right-only changes in output.'
      ImageIndex = imgFavorRight
      ShortCaption = 'Favor Right'
    end
    object IgnoredAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'I&gnored'
      Hint = 'Ignored|Ignores or unignores differences in selected lines or current section.'
      ImageIndex = imgIgnored
      ShortCaption = 'Ignored'
      ToolbarAllowed = False
    end
    object ShowItemNumAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Line &Numbers'
      Hint = 'Line Numbers|Shows or hides line numbers.'
      ImageIndex = imgShowItemNum
      ShortCaption = 'Line #s'
      ToolbarAllowed = False
    end
    object ShowSyntaxHighlightingAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Syntax &Highlighting'
      Hint = 'Syntax Highlighting|Shows or hides syntax highlighting.'
      ImageIndex = imgShowSyntaxHighlighting
      ShortCaption = 'Syntax'
      ToolbarAllowed = False
    end
    object WordWrapAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Word Wra&p'
      Hint = 'Word Wrap|Enables word wrapping in the main file view.'
      ImageIndex = imgWordWrap
      ShortCaption = 'Wrap'
      ToolbarAllowed = False
    end
    object OutputWindowAction: TUiAction
      Category = 'View'
      Caption = 'Detached Out&put Pane'
      Hint = 'Detached Output Pane|Shows output pane in separate window.'
      ImageIndex = imgOutputWindow
    end
    object ZoomAction: TUiAction
      Category = 'View'
      Hint = 'Zoom|Makes current pane larger.'
      ShortCutStr = 'F11'
    end
    object ZoomLeftAction: TUiAction
      Category = 'View'
      Hint = 'Zoom Left|Makes left pane incrementally larger.'
      ShortCutStr = 'Ctrl+Alt+Right'
    end
    object ZoomRightAction: TUiAction
      Category = 'View'
      Hint = 'Zoom Right|Makes right pane incrementally larger.'
      ShortCutStr = 'Ctrl+Alt+Left'
    end
    object WebBrowserAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'We&bpages'
      Hint = 'Webpages|Shows or hides webpage panels.'
      ImageIndex = imgWebBrowser
      ShortCaption = 'Web'
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
    object ShowCenterAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'C&enter Pane'
      Hint = 'Center Pane|Shows or hides center pane.'
      ImageIndex = imgShowCenter
      ShortCaption = 'Center'
      ToolbarAllowed = False
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
    object ShowAlignDetailsAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Alignment Details'
      Hint = 'Alignment Details|Shows or hides alignment details panel.'
      ImageIndex = imgShowAlignDetails
      ShortCaption = 'Alignment'
      ToolbarAllowed = False
    end
    object ShowRulerAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = '&Ruler'
      Hint = 'Ruler|Shows or hides ruler in details panel.'
      ImageIndex = imgShowRuler
      ShortCaption = 'Ruler'
      ToolbarAllowed = False
    end
    object OverwritingAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Hint = 'Overwrite|Typing replaces characters instead of inserting them.'
      MacShortCutStr = 'Ins'
      ShortCutStr = 'Ins'
    end
  end
  object Tree: TUiActionTree
    Nodes = ('File: Menu', ('ExplorerList: SubmenuItem', (), 'Vcs: SeparatorItem', 'CheckIn: MenuItem', 'CheckOut: MenuItem', 'UndoCheckOut: MenuItem', 'ApplyPatch: MenuItem'), 'MergeFile: Menu', ('Info: MenuItem', 'Vcs: SeparatorItem', 'CheckIn: MenuItem', 'CheckOut: MenuItem', 'UndoCheckOut: MenuItem'), 'Edit: Menu', ('Redo: MenuItem', 'Sided: SeparatorItem', 'AlignWith: MenuItem', 'Isolate: MenuItem', 'Replacement: MenuItem', 'CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'CopyItemRight: MenuItem', 'CopyItemLeft: MenuItem', 'CopyItemSide: MenuItem', 'Conflict: MenuItem', 'TakeLeft: MenuItem', 'TakeCenter: MenuItem', 'TakeRight: MenuItem', 'TakeLeftRight: MenuItem', 'TakeRightLeft: MenuItem', 'TakeItemLeft: MenuItem', 'TakeItemCenter: MenuItem', 'TakeItemRight: MenuItem', 'IncreaseIndent: MenuItem', 'DecreaseIndent: MenuItem', 'Paste: MenuItem', 'Delete: MenuItem', 'DeleteItem: MenuItem', 'DeleteItemBegin: MenuItem', 'DeleteItemEnd: MenuItem', 'DeleteWord: MenuItem', 'DeleteWordBegin: MenuItem', 'DeleteWordEnd: MenuItem', 'InsertItemBefore: MenuItem', 'InsertItemAfter: MenuItem', 'SelectAll: MenuItem', 'SelectSection: MenuItem', 'CompareToClipboard: MenuItem', 'Convert: SeparatorItem', 'ConvertList: SubmenuItem', ('TrimTrailWS: MenuItem', 'LeadSpaceToTab: MenuItem', 'TabToSpace: MenuItem', 'EndingStyleList: SubmenuItem', ('ToWindows: MenuItem', 'ToUnix: MenuItem', 'ToMac: MenuItem'))), 'Search: Menu', ('ConflictSectionOffNext: MenuItem', 'ConflictSectionNext: MenuItem', 'ConflictSectionPrev: MenuItem', 'DiffNext: MenuItem', 'DiffPrev: MenuItem', 'DiffSectionNext: MenuItem', 'DiffSectionPrev: MenuItem', 'TakeFileRight: MenuItem', 'DiffReplacedNext: MenuItem', 'DiffReplacedPrev: MenuItem', 'TakenLeftNext: MenuItem', 'TakenLeftPrev: MenuItem', 'TakenRightNext: MenuItem', 'TakenRightPrev: MenuItem', 'Edit: SeparatorItem', 'EditNext: MenuItem', 'EditPrev: MenuItem', 'Find: MenuItem', 'Replace: MenuItem', 'FindPrev: MenuItem', 'FindInFiles: MenuItem', 'MacFindUseSel: MenuItem', 'GoTo: SeparatorItem', 'GoTo: MenuItem', 'Bookmark: SeparatorItem', 'BookmarkToggleList: SubmenuItem', ('BookmarkToggle0: MenuItem', 'BookmarkToggle1: MenuItem', 'BookmarkToggle2: MenuItem', 'BookmarkToggle3: MenuItem', 'BookmarkToggle4: MenuItem', 'BookmarkToggle5: MenuItem', 'BookmarkToggle6: MenuItem', 'BookmarkToggle7: MenuItem', 'BookmarkToggle8: MenuItem', 'BookmarkToggle9: MenuItem'), 'BookmarkGoToList: SubmenuItem', ('BookmarkGoTo0: MenuItem', 'BookmarkGoTo1: MenuItem', 'BookmarkGoTo2: MenuItem', 'BookmarkGoTo3: MenuItem', 'BookmarkGoTo4: MenuItem', 'BookmarkGoTo5: MenuItem', 'BookmarkGoTo6: MenuItem', 'BookmarkGoTo7: MenuItem', 'BookmarkGoTo8: MenuItem', 'BookmarkGoTo9: MenuItem'), 'BookmarkClear: MenuItem'), 'View: Menu', ('FavCompareNone: MenuItem', 'FavMergeAll: MenuItem', 'FavChanged: MenuItem', 'FavConflict: MenuItem', 'FavLeft: MenuItem', 'FavRight: MenuItem', 'FavMergeable: MenuItem', 'FavUnchanged: MenuItem', 'FavMergeNone: MenuItem', 'InsigIgnored: SeparatorItem', 'ShowContext: MenuItem', 'SameModIgnored: MenuItem', 'FavorLeft: MenuItem', 'FavorRight: MenuItem', 'Ignored: SeparatorItem', 'Ignored: MenuItem', 'ShowWS: MenuItem', 'ShowItemNum: MenuItem', 'ShowSyntaxHighlighting: MenuItem', 'WordWrap: MenuItem', 'OverUnder: MenuItem', 'OutputWindow: MenuItem', 'WebBrowser: MenuItem', 'ShowThumbnail: MenuItem', 'ShowCenter: MenuItem', 'ShowTextDetails: MenuItem', 'ShowHexDetails: MenuItem', 'ShowAlignDetails: MenuItem', 'ShowRuler: MenuItem'), 'Main: Toolbar', ('FavCompareNone: ToolButton', 'FavMergeAll: ToolButton', 'DisplayFilters: SubmenuButton', ('FavChanged: MenuItem', 'FavConflict: MenuItem', 'FavLeft: MenuItem', 'FavRight: MenuItem', 'FavMergeable: MenuItem'), 'FavChanged: ToolButton', 'FavConflict: ToolButton', 'FavLeft: ToolButton', 'FavRight: ToolButton', 'FavMergeable: ToolButton', 'FavUnchanged: ToolButton', 'FavMergeNone: ToolButton', 'TogDiff: ToolButton', 'TogNoMod: ToolButton', 'TogSameMod: ToolButton', 'TogLeftMod: ToolButton', 'TogRightMod: ToolButton', 'TogDiffMod: ToolButton', 'TogConflict: ToolButton', 'InsigIgnored: SeparatorButton', 'ShowContext: ToolButton', 'SameModIgnored: ToolButton', 'FavorLeft: ToolButton', 'FavorRight: ToolButton', 'Redo: ToolButton', 'CopyRight: ToolButton', 'CopyLeft: ToolButton', 'CopySide: ToolButton', 'CopyItemRight: ToolButton', 'CopyItemLeft: ToolButton', 'CopyItemSide: ToolButton', 'Conflict: ToolButton', 'TakeLeft: ToolButton', 'TakeCenter: ToolButton', 'TakeRight: ToolButton', 'Cut: ToolButton', 'Copy: ToolButton', 'Paste: ToolButton', 'Delete: ToolButton', 'Search: SeparatorButton', 'ConflictSectionOffNext: ToolButton', 'ConflictSectionNext: ToolButton', 'ConflictSectionPrev: ToolButton', 'DiffSectionNext: ToolButton', 'DiffSectionPrev: ToolButton', 'Find: ToolButton', 'Replace: ToolButton', 'FindPrev: ToolButton', 'GoTo: ToolButton', 'View: SeparatorButton', 'Ignored: ToolButton', 'ShowWS: ToolButton', 'ShowItemNum: ToolButton', 'ShowSyntaxHighlighting: ToolButton', 'WordWrap: ToolButton', 'OverUnder: ToolButton', 'WebBrowser: ToolButton', 'ShowThumbnail: ToolButton', 'ShowCenter: ToolButton', 'ShowTextDetails: ToolButton', 'ShowHexDetails: ToolButton', 'ShowAlignDetails: ToolButton', 'ShowRuler: ToolButton'), 'Edit: PopupMenu', ('AlignWith: MenuItem', 'Isolate: MenuItem', 'Replacement: MenuItem', 'CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'CopyItemRight: MenuItem', 'CopyItemLeft: MenuItem', 'CopyItemSide: MenuItem', 'IncreaseIndent: MenuItem', 'DecreaseIndent: MenuItem', 'N1: SeparatorItem', 'Cut: MenuItem', 'Copy: MenuItem', 'Paste: MenuItem', 'Delete: MenuItem', 'DeleteItem: MenuItem', 'DeleteItemBegin: MenuItem', 'DeleteItemEnd: MenuItem', 'DeleteWord: MenuItem', 'DeleteWordBegin: MenuItem', 'DeleteWordEnd: MenuItem', 'InsertItemBefore: MenuItem', 'InsertItemAfter: MenuItem', 'N2: SeparatorItem', 'SelectSection: MenuItem', 'CompareToClipboard: MenuItem', 'N3: SeparatorItem', 'Ignored: MenuItem', 'N4: SeparatorItem', 'New: MenuItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenClipboard: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem', 'OpenTextPatch: MenuItem'), 'Save: MenuItem', 'SaveAs: MenuItem', 'SaveAsLocal: MenuItem', 'SaveAsProfile: MenuItem', 'ExplorerList: SubmenuItem', (), 'N5: SeparatorItem', 'CheckIn: MenuItem', 'CheckOut: MenuItem', 'UndoCheckOut: MenuItem'), 'LeftEdit: PopupMenu', ('AlignWith: MenuItem', 'Isolate: MenuItem', 'Conflict: MenuItem', 'TakeLeft: MenuItem', 'TakeLeftRight: MenuItem', 'TakeRightLeft: MenuItem', 'TakeItemLeft: MenuItem', 'N1: SeparatorItem', 'Copy: MenuItem', 'N2: SeparatorItem', 'SelectSection: MenuItem', 'CompareToClipboard: MenuItem', 'N3: SeparatorItem', 'Ignored: MenuItem', 'N4: SeparatorItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenClipboard: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem', 'OpenTextPatch: MenuItem'), 'SaveAs: MenuItem', 'SaveAsLocal: MenuItem', 'SaveAsProfile: MenuItem', 'ExplorerList: SubmenuItem', ()), 'CenterEdit: PopupMenu', ('AlignWith: MenuItem', 'Isolate: MenuItem', 'Conflict: MenuItem', 'TakeCenter: MenuItem', 'TakeLeftRight: MenuItem', 'TakeRightLeft: MenuItem', 'TakeItemCenter: MenuItem', 'N1: SeparatorItem', 'Copy: MenuItem', 'N2: SeparatorItem', 'SelectSection: MenuItem', 'CompareToClipboard: MenuItem', 'N3: SeparatorItem', 'Ignored: MenuItem', 'N4: SeparatorItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenClipboard: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem', 'OpenTextPatch: MenuItem'), 'SaveAs: MenuItem', 'SaveAsLocal: MenuItem', 'SaveAsProfile: MenuItem', 'ExplorerList: SubmenuItem', ()), 'RightEdit: PopupMenu', ('AlignWith: MenuItem', 'Isolate: MenuItem', 'Conflict: MenuItem', 'TakeRight: MenuItem', 'TakeLeftRight: MenuItem', 'TakeRightLeft: MenuItem', 'TakeItemRight: MenuItem', 'N1: SeparatorItem', 'Copy: MenuItem', 'N2: SeparatorItem', 'SelectSection: MenuItem', 'CompareToClipboard: MenuItem', 'N3: SeparatorItem', 'Ignored: MenuItem', 'N4: SeparatorItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenClipboard: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem', 'OpenTextPatch: MenuItem'), 'SaveAs: MenuItem', 'SaveAsLocal: MenuItem', 'SaveAsProfile: MenuItem', 'ExplorerList: SubmenuItem', ()), 'OutputEdit: PopupMenu', ('Conflict: MenuItem', 'TakeLeft: MenuItem', 'TakeCenter: MenuItem', 'TakeRight: MenuItem', 'TakeLeftRight: MenuItem', 'TakeRightLeft: MenuItem', 'TakeItemLeft: MenuItem', 'TakeItemCenter: MenuItem', 'TakeItemRight: MenuItem', 'IncreaseIndent: MenuItem', 'DecreaseIndent: MenuItem', 'N1: SeparatorItem', 'Cut: MenuItem', 'Copy: MenuItem', 'Paste: MenuItem', 'Delete: MenuItem', 'DeleteItem: MenuItem', 'DeleteItemBegin: MenuItem', 'DeleteItemEnd: MenuItem', 'DeleteWord: MenuItem', 'DeleteWordBegin: MenuItem', 'DeleteWordEnd: MenuItem', 'InsertItemBefore: MenuItem', 'InsertItemAfter: MenuItem', 'N2: SeparatorItem', 'SelectSection: MenuItem', 'CompareToClipboard: MenuItem', 'N3: SeparatorItem', 'Ignored: MenuItem', 'N4: SeparatorItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem', 'N1: SeparatorItem', 'OpenTextEdit: MenuItem', 'OpenTextPatch: MenuItem'), 'Save: MenuItem', 'SaveAs: MenuItem', 'SaveAsLocal: MenuItem', 'SaveAsProfile: MenuItem', 'ExplorerList: SubmenuItem', ()), 'DetailsEdit: PopupMenu', ('Cut: MenuItem', 'Copy: MenuItem', 'Paste: MenuItem', 'Delete: MenuItem', 'DeleteItemBegin: MenuItem', 'DeleteItemEnd: MenuItem', 'DeleteWord: MenuItem', 'DeleteWordBegin: MenuItem', 'DeleteWordEnd: MenuItem'), 'InputDetailsEdit: PopupMenu', ('Copy: MenuItem'), 'Gutter: PopupMenu', ('CopyRight: MenuItem', 'CopyLeft: MenuItem', 'CopySide: MenuItem', 'CopyItemRight: MenuItem', 'CopyItemLeft: MenuItem', 'CopyItemSide: MenuItem', 'N1: SeparatorItem', 'ShowItemNum: MenuItem', 'N2: SeparatorItem', 'BookmarkToggleList: SubmenuItem', ('BookmarkToggle0: MenuItem', 'BookmarkToggle1: MenuItem', 'BookmarkToggle2: MenuItem', 'BookmarkToggle3: MenuItem', 'BookmarkToggle4: MenuItem', 'BookmarkToggle5: MenuItem', 'BookmarkToggle6: MenuItem', 'BookmarkToggle7: MenuItem', 'BookmarkToggle8: MenuItem', 'BookmarkToggle9: MenuItem'), 'BookmarkGoToList: SubmenuItem', ('BookmarkGoTo0: MenuItem', 'BookmarkGoTo1: MenuItem', 'BookmarkGoTo2: MenuItem', 'BookmarkGoTo3: MenuItem', 'BookmarkGoTo4: MenuItem', 'BookmarkGoTo5: MenuItem', 'BookmarkGoTo6: MenuItem', 'BookmarkGoTo7: MenuItem', 'BookmarkGoTo8: MenuItem', 'BookmarkGoTo9: MenuItem'), 'BookmarkClear: MenuItem'))
  end
end
