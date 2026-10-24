object FileCodePageErrorDialog: TFileCodePageErrorDialog
  Caption = 'Encoding Error'
  ClientHeight = 119
  ClientWidth = 401
  PixelsPerInch = 96
  TextHeight = 13
  object Lbl: TUiLabel
    Left = 8
    Top = 8
    Width = 385
    Height = 26
    Caption = 'This file contains Unicode characters that will be lost if it is saved using the current encoding.'
    WordWrap = True
  end
  object CodePageLbl: TUiLabel
    Left = 8
    Top = 42
    Height = 13
    Caption = '&Encoding:'
    FocusControl = CodePageEdit
  end
  object CodePageEdit: TUiCodePageEdit
    Left = 8
    Top = 59
    Width = 385
    Height = 21
    TabOrder = 0
    AllowDetect = False
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 80
    Width = 401
    TabOrder = 1
    object OkBtn: TUiOkBtn
      Caption = '&Save'
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
