object TableColHandlingDialog: TTableColHandlingDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgTableColHandling'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = '%'
  ClientHeight = 194
  ClientWidth = 410
  PixelsPerInch = 96
  TextHeight = 13
  object AsTextLbl: TUiLabel
    Left = 8
    Top = 58
    Height = 13
    Caption = '&Type:'
    FocusControl = AsTextEdit
  end
  object StrInsigLbl: TUiLabel
    Left = 209
    Top = 8
    Height = 13
    Caption = 'Text important, except for:'
  end
  object DateTimeToleranceLbl: TUiLabel
    Left = 209
    Top = 71
    Height = 13
    Caption = 'Dat&e tolerance:'
    FocusControl = DateTimeToleranceEdit
  end
  object NumToleranceLbl: TUiLabel
    Left = 209
    Top = 117
    Height = 13
    Caption = '&Numeric tolerance:'
    FocusControl = NumToleranceEdit
  end
  object IsKeyEdit: TUiCheckBox
    Left = 8
    Top = 8
    Height = 17
    Caption = '&Key'
    TabOrder = 0
    OnClick = SomethingChangedClick
  end
  object UseDefaultEdit: TUiCheckBox
    Left = 8
    Top = 33
    Height = 17
    Caption = 'Use &default'
    TabOrder = 1
    OnClick = UseDefaultClick
  end
  object AsTextEdit: TUiComboBox
    Left = 8
    Top = 75
    Width = 193
    Height = 21
    Style = csDropDownList
    TabOrder = 2
    OnChange = SomethingChangedClick
    Items.Strings = ('General', 'Text')
  end
  object InsigEdit: TUiCheckBox
    Left = 8
    Top = 104
    Height = 17
    Caption = '&Unimportant'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object StrCaseInsigEdit: TUiCheckBox
    Left = 209
    Top = 25
    Height = 17
    Caption = 'Character &case (ABC = abc)'
    TabOrder = 4
    OnClick = SomethingChangedClick
  end
  object StrWSInsigEdit: TUiCheckBox
    Left = 209
    Top = 46
    Height = 17
    Caption = '&Whitespace'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
  object DateTimeToleranceEdit: TUiSpinEdit
    Left = 209
    Top = 88
    Width = 65
    Height = 21
    TabOrder = 6
    OnChange = SomethingChangedClick
  end
  object DateTimeToleranceKindEdit: TUiComboBox
    Left = 282
    Top = 88
    Width = 120
    Height = 21
    Style = csDropDownList
    TabOrder = 7
    OnChange = SomethingChangedClick
    Items.Strings = ('seconds', 'minutes', 'hours', 'days')
  end
  object NumToleranceEdit: TUiNumEdit
    Left = 209
    Top = 134
    Width = 65
    Height = 21
    Kind = numFloat
    TabOrder = 8
    OnChange = SomethingChangedClick
  end
  object NumToleranceRelativeEdit: TUiComboBox
    Left = 282
    Top = 134
    Width = 120
    Height = 21
    Style = csDropDownList
    TabOrder = 9
    OnChange = SomethingChangedClick
    Items.Strings = ('absolute', 'relative (%)')
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 155
    Width = 410
    TabOrder = 10
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
