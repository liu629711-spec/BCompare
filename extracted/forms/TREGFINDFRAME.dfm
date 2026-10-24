object RegFindFrame: TRegFindFrame
  object FindPrevBtn: TUiButton
    TabOrder = 6
  end
  object FindNextBtn: TUiButton
    TabOrder = 7
  end
  object ReplaceBtn: TUiButton
    TabOrder = 8
  end
  object ReplaceAllBtn: TUiButton
    TabOrder = 9
  end
  object SelectAllBtn: TUiButton
    TabOrder = 10
  end
  object AutoCloseEdit: TUiCheckBox
    TabOrder = 11
  end
  object InKeyEdit: TUiCheckBox
    Left = 231
    Top = 59
    Height = 17
    Caption = '&Keys'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object InValueEdit: TUiCheckBox
    Left = 275
    Top = 59
    Height = 17
    Caption = '&Values'
    TabOrder = 4
    OnClick = SomethingChangedClick
  end
  object InDataEdit: TUiCheckBox
    Left = 327
    Top = 59
    Height = 17
    Caption = '&Data'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
end
