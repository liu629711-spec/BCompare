object VfsDropboxAuthCodeDialog: TVfsDropboxAuthCodeDialog
  Caption = 'Dropbox Authorization'
  ClientHeight = 85
  ClientWidth = 387
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object AuthCodeLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Enter authorization code here after authenticating with Dropbox:'
    FocusControl = AuthCodeEdit
  end
  object AuthCodeEdit: TUiEdit
    Left = 8
    Top = 25
    Width = 371
    Height = 21
    TabOrder = 0
    OnChange = AuthCodeEditChange
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 46
    Width = 387
    TabOrder = 1
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
