object VfsAmazonS3LoginDialog: TVfsAmazonS3LoginDialog
  Caption = 'Authentication Required'
  ClientHeight = 160
  ClientWidth = 435
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object PromptLbl: TUiLabel
    Left = 8
    Top = 8
    Width = 419
    Height = 13
    Caption = '%'
    WordWrap = True
  end
  object AccessKeyIDLbl: TUiLabel
    Left = 8
    Top = 29
    Height = 13
    Caption = 'Access key &ID:'
    FocusControl = AccessKeyIDEdit
  end
  object SecretAccessKeyLbl: TUiLabel
    Left = 8
    Top = 75
    Height = 13
    Caption = '&Secret access key:'
    FocusControl = SecretAccessKeyEdit
  end
  object AccessKeyIDEdit: TUiEdit
    Left = 8
    Top = 46
    Width = 419
    Height = 21
    TabOrder = 0
  end
  object SecretAccessKeyEdit: TUiEdit
    Left = 8
    Top = 92
    Width = 419
    Height = 21
    TabOrder = 1
    EchoMode = emPassword
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 121
    Width = 435
    TabOrder = 2
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
