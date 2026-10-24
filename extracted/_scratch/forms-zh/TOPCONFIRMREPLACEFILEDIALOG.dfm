object OpConfirmReplaceFileDialog: TOpConfirmReplaceFileDialog
  Caption = 'Confirm File Replace'
  ClientHeight = 234
  ClientWidth = 425
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object ConfirmLbl: TUiLabel
    Left = 64
    Top = 16
    Width = 353
    Height = 13
    Caption = '%'
    ShowAccelChar = False
    WordWrap = True
  end
  object TgtLbl: TUiLabel
    Left = 64
    Top = 63
    Height = 13
    Caption = 'Would you like to replace the existing file'
  end
  object TgtPathLbl: TUiLabel
    Left = 80
    Top = 80
    Width = 337
    Height = 13
    AutoSize = False
    Caption = '%'
    ShowAccelChar = False
  end
  object TgtSizeLbl: TUiLabel
    Left = 80
    Top = 97
    Height = 13
    Caption = '%'
  end
  object TgtLastModLbl: TUiLabel
    Left = 80
    Top = 114
    Height = 13
    Caption = '%'
  end
  object SrcLbl: TUiLabel
    Left = 64
    Top = 131
    Height = 13
    Caption = 'with this one?'
  end
  object SrcPathLbl: TUiLabel
    Left = 80
    Top = 148
    Width = 337
    Height = 13
    AutoSize = False
    Caption = '%'
    ShowAccelChar = False
  end
  object SrcSizeLbl: TUiLabel
    Left = 80
    Top = 165
    Height = 13
    Caption = '%'
  end
  object SrcLastModLbl: TUiLabel
    Left = 80
    Top = 182
    Height = 13
    Caption = '%'
  end
  object Image: TUiDlgIcon
    Left = 16
    Top = 16
    IconType = diWarning
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 195
    Width = 425
    TabOrder = 0
    object YesBtn: TUiYesBtn
    end
    object YesToAllBtn: TUiYesToAllBtn
    end
    object NoBtn: TUiNoBtn
      Default = True
    end
    object NoToAllBtn: TUiNoToAllBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
