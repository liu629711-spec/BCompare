object ExternalFormatGeneralFrame: TExternalFormatGeneralFrame
  HelpType = htKeyword
  HelpKeyword = 'FormatExternalGeneral'
  object DescriptionLbl: TUiLabel
    Top = 240
  end
  object QuickCompareCmdLineLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = '&Quick compare command line:'
    FocusControl = QuickCompareCmdLineEdit
  end
  object ViewCmdLineLbl: TUiLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = 'Compare &view command line:'
    FocusControl = ViewCmdLineEdit
  end
  object QuickMergeCmdLineLbl: TUiLabel
    Left = 8
    Top = 146
    Height = 13
    Caption = 'Q&uick merge command line:'
    FocusControl = QuickMergeCmdLineEdit
  end
  object ViewMergeCmdLineLbl: TUiLabel
    Left = 8
    Top = 192
    Height = 13
    Caption = 'Merge vie&w command line:'
    FocusControl = ViewMergeCmdLineEdit
  end
  object DescriptionEdit: TUiMemo
    Top = 257
    Height = 56
    TabOrder = 5
  end
  object QuickCompareCmdLineEdit: TUiSpecBar
    Left = 8
    Top = 71
    Width = 257
    TabOrder = 1
    OnBrowse = CmdLineEditBrowse
    OnChange = SomethingChangedClick
    OnGetArgs = CompareCmdLineEditGetArgs
  end
  object ViewCmdLineEdit: TUiSpecBar
    Left = 8
    Top = 117
    Width = 257
    TabOrder = 2
    OnBrowse = CmdLineEditBrowse
    OnChange = SomethingChangedClick
    OnGetArgs = CompareCmdLineEditGetArgs
  end
  object QuickMergeCmdLineEdit: TUiSpecBar
    Left = 8
    Top = 163
    Width = 257
    TabOrder = 3
    OnBrowse = CmdLineEditBrowse
    OnChange = SomethingChangedClick
    OnGetArgs = MergeCmdLineEditGetArgs
  end
  object ViewMergeCmdLineEdit: TUiSpecBar
    Left = 8
    Top = 209
    Width = 257
    TabOrder = 4
    OnBrowse = CmdLineEditBrowse
    OnChange = SomethingChangedClick
    OnGetArgs = MergeCmdLineEditGetArgs
  end
end
