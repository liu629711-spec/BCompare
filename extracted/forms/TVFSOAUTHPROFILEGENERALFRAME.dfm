object VfsOAuthProfileGeneralFrame: TVfsOAuthProfileGeneralFrame
  HelpType = htKeyword
  Caption = 'General'
  object DisplayNameLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Name:'
  end
  object DisplayNameEdit: TUiLabel
    Left = 8
    Top = 25
    Width = 239
    Height = 13
    AutoSize = False
    Caption = '%'
  end
  object EmailLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = 'Email:'
  end
  object EmailEdit: TUiLabel
    Left = 8
    Top = 71
    Width = 239
    Height = 13
    AutoSize = False
    Caption = '%'
  end
  object DescriptionLbl: TUiLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = 'D&escription:'
    FocusControl = DescriptionEdit
  end
  object DescriptionEdit: TUiMemo
    Left = 8
    Top = 117
    Width = 239
    Height = 184
    ScrollBars = ssVertical
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
end
