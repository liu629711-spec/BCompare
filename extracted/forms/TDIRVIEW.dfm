object DirView: TDirView
  HelpType = htKeyword
  HelpKeyword = 'ViewDir'
  object LogFrame: TLogFrame
    object ListBox: TUiVirtualListBox
      PopupMenu = LogPopup
    end
  end
end
