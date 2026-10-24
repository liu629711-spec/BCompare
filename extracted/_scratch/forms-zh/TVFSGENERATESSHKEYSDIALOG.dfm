object VfsGenerateSSHKeysDialog: TVfsGenerateSSHKeysDialog
  ActiveControl = PassphraseEdit
  Caption = 'Generate SSH Key Pair'
  ClientHeight = 307
  ClientWidth = 313
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object KeyTypeLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Key type:'
    FocusControl = KeyTypeEdit
  end
  object KeyLengthLbl: TUiLabel
    Left = 164
    Top = 8
    Height = 13
    Caption = '%'
    FocusControl = KeyLengthEdit
  end
  object CommentLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = '&Comment:'
    FocusControl = CommentEdit
  end
  object PassphraseLbl: TUiLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = '&Passphrase:'
    FocusControl = PassphraseEdit
  end
  object PassphraseMismatchLbl: TUiLabel
    Left = 156
    Top = 100
    Width = 149
    Height = 13
    Alignment = taRightJustify
    Caption = 'Passphrases do not match'
    FontStyle = [fsBold]
  end
  object ConfirmPassphraseLbl: TUiLabel
    Left = 8
    Top = 146
    Height = 13
    Caption = 'C&onfirm passphrase:'
    FocusControl = ConfirmPassphraseEdit
  end
  object PrivateKeyFileLbl: TUiLabel
    Left = 8
    Top = 192
    Height = 13
    Caption = 'P&rivate key filename:'
    FocusControl = PrivateKeyFileEdit
  end
  object PublicKeyFileLbl: TUiLabel
    Left = 8
    Top = 238
    Height = 13
    Caption = 'Public key filename:'
  end
  object PublicKeyFileEdit: TUiLabel
    Left = 8
    Top = 255
    Width = 297
    Height = 13
    AutoSize = False
    Caption = '%'
    EllipsisPosition = epPathEllipsis
  end
  object KeyTypeEdit: TUiComboBox
    Left = 8
    Top = 25
    Width = 67
    Height = 21
    Style = csDropDownList
    TabOrder = 0
    OnChange = KeyTypeEditChange
  end
  object KeyLengthEdit: TUiComboBox
    Left = 164
    Top = 25
    Width = 65
    Height = 21
    MaxLength = 4
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object CommentEdit: TUiEdit
    Left = 8
    Top = 71
    Width = 297
    Height = 21
    TabOrder = 2
  end
  object PassphraseEdit: TUiEdit
    Left = 8
    Top = 117
    Width = 297
    Height = 21
    TabOrder = 3
    OnChange = PassphraseEditChange
    EchoMode = emPassword
  end
  object ConfirmPassphraseEdit: TUiEdit
    Left = 8
    Top = 165
    Width = 297
    Height = 21
    TabOrder = 4
    OnChange = PassphraseEditChange
    EchoMode = emPassword
  end
  object PrivateKeyFileEdit: TUiSpecBar
    Left = 8
    Top = 209
    Width = 297
    TabOrder = 5
    OnBrowse = PrivateKeyFileEditBrowse
    OnChange = PrivateKeyFileEditChange
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 268
    Width = 313
    TabOrder = 6
    object OkBtn: TUiOkBtn
      Caption = '&Generate'
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
