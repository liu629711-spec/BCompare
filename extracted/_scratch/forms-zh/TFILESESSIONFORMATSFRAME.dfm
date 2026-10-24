object FileSessionFormatsFrame: TFileSessionFormatsFrame
  Caption = 'Format'
  object LeftLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '%'
    FocusControl = LeftEdit
  end
  object RightLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = '&Right file format:'
    FocusControl = RightEdit
  end
  object LeftEdit: TUiComboBox
    Left = 8
    Top = 25
    Width = 409
    Height = 21
    Style = csDropDownList
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object RightEdit: TUiComboBox
    Left = 8
    Top = 71
    Width = 409
    Height = 21
    Style = csDropDownList
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object SameAsLeftEdit: TUiCheckBox
    Left = 8
    Top = 100
    Height = 17
    Caption = 'Sa&me as left file format'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
end
