object RegisterDialog: TRegisterDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgRegister'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Register Beyond Compare'
  ClientHeight = 259
  ClientWidth = 465
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object PromptLbl: TUiLabel
    Left = 8
    Top = 194
    Width = 449
    Height = 13
    Caption = '%'
    WordWrap = True
  end
  object KeyMemo: TUiMemo
    Left = 8
    Top = 8
    Width = 449
    Height = 153
    ScrollBars = ssVertical
    TabOrder = 0
    WantReturns = False
  end
  object AllUsersEdit: TUiCheckBox
    Left = 8
    Top = 169
    Height = 17
    Caption = 'Register for &all users'
    TabOrder = 1
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 220
    Width = 465
    TabOrder = 2
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
    object HelpBtn: TUiHelpBtn
    end
  end
end
