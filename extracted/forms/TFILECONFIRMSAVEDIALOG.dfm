object FileConfirmSaveDialog: TFileConfirmSaveDialog
  Caption = '%'
  ClientHeight = 154
  ClientWidth = 353
  OnClose = FormClose
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiDlgIcon
    Left = 16
    Top = 16
    IconType = diWarning
  end
  object ConfirmLbl: TUiLabel
    Left = 64
    Top = 24
    Height = 13
    Caption = 'Save changes?'
  end
  object LeftEdit: TUiCheckBox
    Left = 64
    Top = 56
    Height = 17
    Caption = '&Left file'
    TabOrder = 0
  end
  object RightEdit: TUiCheckBox
    Left = 64
    Top = 77
    Height = 17
    Caption = '&Right file'
    TabOrder = 1
  end
  object CenterEdit: TUiCheckBox
    Left = 64
    Top = 98
    Height = 17
    Caption = '&Center file'
    TabOrder = 2
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 115
    Width = 353
    TabOrder = 3
    object YesBtn: TUiYesBtn
      Caption = '&Save Checked'
      Default = True
    end
    object NoBtn: TUiNoBtn
      Caption = '&Discard All'
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
