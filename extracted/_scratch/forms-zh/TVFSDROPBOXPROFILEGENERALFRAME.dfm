object VfsDropboxProfileGeneralFrame: TVfsDropboxProfileGeneralFrame
  HelpKeyword = 'ProfileDropbox'
  object DescriptionLbl: TUiLabel
    Top = 146
  end
  object PathRootLbl: TUiLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = '&Root folder:'
  end
  object ThrobberImage: TImage
    Left = 152
    Top = 8
    Width = 32
    Height = 32
    Picture.Data = {TPngImage 596 bytes}
    Visible = False
  end
  object ThrobberBox: TPaintBox
    Left = 231
    Top = 8
    Width = 16
    Height = 16
    OnPaint = ThrobberBoxPaint
  end
  object DescriptionEdit: TUiMemo
    Top = 163
    Height = 138
    TabOrder = 1
  end
  object PathRootEdit: TUiComboBox
    Left = 8
    Top = 117
    Width = 239
    Height = 21
    Style = csDropDownList
    Color = clBtnFace
    Enabled = False
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object ThrobberTimer: TTimer
    Enabled = False
    OnTimer = ThrobberTimerTimer
    Left = 192
    Top = 8
  end
end
