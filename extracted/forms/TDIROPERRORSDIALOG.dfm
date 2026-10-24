object DirOpErrorsDialog: TDirOpErrorsDialog
  BorderStyle = bsSizeable
  Caption = 'File Operation Errors'
  ClientHeight = 295
  ClientWidth = 337
  Constraints.MinHeight = 127
  Constraints.MinWidth = 105
  PixelsPerInch = 96
  TextHeight = 13
  object LeftBevel: TUiBevel
    Left = 0
    Top = 32
    Width = 8
    Height = 224
    Align = alLeft
    Shape = bsSpacer
  end
  object RightBevel: TUiBevel
    Left = 329
    Top = 32
    Width = 8
    Height = 224
    Align = alRight
    Shape = bsSpacer
  end
  object TopPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 337
    Height = 32
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
    object ProblemsImage: TUiImage
      Left = 8
      Top = 8
      Width = 16
      Height = 16
      ImageIndex = imgError
      Images = BcImages.MainImages
    end
    object ProblemsLbl: TUiLabel
      Left = 32
      Top = 8
      Height = 13
      Caption = 'Problems:'
    end
  end
  object ErrorsEdit: TUiMemo
    Left = 8
    Top = 32
    Width = 321
    Height = 224
    Align = alClient
    ReadOnly = True
    ScrollBars = ssVertical
    TabOrder = 1
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 256
    Width = 337
    TabOrder = 2
    SizeGripper = True
    object CloseBtn: TUiCloseBtn
    end
  end
end
