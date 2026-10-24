object OpenWithItemDialog: TOpenWithItemDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgOpenWithItem'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = '"Open With" Application'
  ClientHeight = 262
  ClientWidth = 408
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object DescriptionLbl: TUiLabel
    Left = 8
    Top = 17
    Height = 13
    Caption = 'D&escription:'
    FocusControl = DescriptionEdit
  end
  object ShortCutLbl: TUiLabel
    Left = 176
    Top = 17
    Height = 13
    Caption = '&Shortcut:'
    FocusControl = ShortCutEdit
  end
  object CmdLineLbl: TUiLabel
    Left = 8
    Top = 59
    Height = 13
    Caption = 'C&ommand line:'
    FocusControl = CmdLineEdit
  end
  object WorkingDirLbl: TUiLabel
    Left = 8
    Top = 101
    Height = 13
    Caption = 'Wor&king folder:'
    FocusControl = WorkingDirEdit
  end
  object PathDelimLbl: TUiLabel
    Left = 296
    Top = 101
    Height = 13
    Caption = '&Path delimiter:'
    FocusControl = PathDelimEdit
  end
  object DescriptionEdit: TUiEdit
    Left = 8
    Top = 34
    Width = 158
    Height = 21
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object ShortCutEdit: TUiShortCutEdit
    Left = 174
    Top = 34
    Width = 145
    Height = 21
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object ShortCutRemoveBtn: TUiButton
    Left = 327
    Top = 34
    Caption = '&Remove'
    TabOrder = 2
    OnClick = ShortCutRemoveClick
    AutoSize = asRight
  end
  object CmdLineEdit: TUiSpecBar
    Left = 8
    Top = 76
    Width = 392
    TabOrder = 3
    OnBrowse = CmdLineEditBrowse
    OnChange = SomethingChangedClick
    OnGetArgs = CmdLineEditGetArgs
  end
  object WorkingDirEdit: TUiSpecComboBar
    Left = 8
    Top = 118
    Width = 280
    AutoCompleteEx = acDirs
    IsMRU = False
    TabOrder = 4
    OnBrowse = WorkingDirEditBrowse
    OnChange = SomethingChangedClick
  end
  object PathDelimEdit: TUiEdit
    Left = 296
    Top = 118
    Width = 24
    Height = 21
    MaxLength = 2
    TabOrder = 5
    OnChange = SomethingChangedClick
  end
  object HandleFilesEdit: TUiCheckBox
    Left = 8
    Top = 143
    Height = 17
    Caption = 'Accepts &files'
    TabOrder = 6
    OnClick = HandleClick
  end
  object HandleFoldersEdit: TUiCheckBox
    Left = 208
    Top = 143
    Height = 17
    Caption = 'Accepts fo&lders'
    TabOrder = 7
    OnClick = HandleClick
  end
  object RefreshWhenDoneEdit: TUiCheckBox
    Left = 8
    Top = 164
    Height = 17
    Caption = 'Refres&h when finished'
    TabOrder = 8
    OnClick = SomethingChangedClick
  end
  object MultiInstanceEdit: TUiCheckBox
    Left = 8
    Top = 185
    Height = 17
    Caption = '&Multiple instances'
    TabOrder = 9
    OnClick = SomethingChangedClick
  end
  object WaitForEdit: TUiCheckBox
    Left = 24
    Top = 206
    Height = 17
    Caption = '&Wait for previous instance to finish'
    TabOrder = 10
    OnClick = SomethingChangedClick
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 223
    Width = 408
    TabOrder = 11
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
