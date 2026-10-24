object VfsSftpPassphraseDialog: TVfsSftpPassphraseDialog
  Caption = 'Enter Passphrase'
  ClientHeight = 140
  ClientWidth = 417
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object TopBevel: TUiBevel
    Left = 0
    Top = 0
    Width = 417
    Height = 8
    Align = alTop
    Shape = bsSpacer
  end
  object InvalidLbl: TUiLabel
    Left = 0
    Top = 8
    Height = 13
    Align = alTop
    Alignment = taCenter
    Caption = 'Passphrase is incorrect.'
    FontColor = clRed
  end
  object CommentLbl: TUiLabel
    Left = 8
    Top = 25
    Height = 13
    Caption = 'Private key:'
  end
  object CommentEdit: TUiLabel
    Left = 8
    Top = 42
    Width = 401
    Height = 13
    AutoSize = False
    Caption = '%'
    EllipsisPosition = epPathEllipsis
  end
  object PassphraseLbl: TUiLabel
    Left = 8
    Top = 63
    Height = 13
    Caption = '&SSH private key passphrase:'
    FocusControl = PassphraseEdit
  end
  object PassphraseEdit: TUiEdit
    Left = 8
    Top = 80
    Width = 401
    Height = 21
    TabOrder = 0
    EchoMode = emPassword
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 101
    Width = 417
    TabOrder = 1
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
