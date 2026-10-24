object DirOpProgressFrame: TDirOpProgressFrame
  Left = 0
  Top = 0
  Width = 583
  Height = 38
  TabOrder = 0
  Visible = False
  object ProgressImage: TUiImage
    Left = 240
    Top = 4
    Width = 17
    Height = 16
    Center = True
    Images = BcImages.MainImages
  end
  object ProgressLbl: TUiLabel
    Left = 261
    Top = 4
    Width = 295
    Height = 13
    AutoSize = False
    Caption = '%'
    ShowAccelChar = False
  end
  object RemainingLbl: TUiLabel
    Left = 564
    Top = 4
    Height = 13
    Caption = '%'
    ShowAccelChar = False
  end
  object ErrorImage: TUiImage
    Left = 52
    Top = 21
    Width = 16
    Height = 16
    ImageIndex = imgError
    Images = BcImages.MainImages
  end
  object ErrorCountLinkLbl: TUiLinkLabel
    Left = 72
    Top = 21
    Height = 13
    Hint = 'View all errors in a popup window'
    Caption = '%'
    OnClick = ErrorCountLinkClick
  end
  object ErrorLbl: TUiLabel
    Left = 261
    Top = 21
    Height = 13
    Caption = '%'
    ShowAccelChar = False
  end
  object CancelBtn: TUiBitBtn
    Left = 0
    Top = 0
    Width = 22
    Height = 21
    Hint = 'Stop|Stops operation.'
    ImageIndex = imgStopRed
    Images = BcImages.MainImages
    TabOrder = 0
    OnClick = CancelClick
  end
  object PauseBtn: TUiBitBtn
    Left = 26
    Top = 0
    Width = 22
    Height = 21
    ImageIndex = imgMediaPause
    Images = BcImages.MainImages
    TabOrder = 1
    OnClick = PauseClick
  end
  object ProgressBar: TUiProgressBar
    Left = 52
    Top = 2
    Width = 184
    Height = 17
    TabOrder = 2
  end
end
