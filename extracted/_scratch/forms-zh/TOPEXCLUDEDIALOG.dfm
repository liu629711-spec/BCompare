object OpExcludeDialog: TOpExcludeDialog
  HelpType = htKeyword
  HelpKeyword = 'OpExclude'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Exclude from Session'
  ClientHeight = 143
  ClientWidth = 393
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object TopLineBevel: TUiBevel
    Left = 8
    Top = 54
    Width = 377
    Height = 2
    Shape = bsTopLine
  end
  object SelFilenamesEdit: TUiRadioButton
    Left = 8
    Top = 8
    Height = 17
    Caption = '&Selected filename(s)'
    Checked = True
    TabOrder = 0
    TabStop = True
  end
  object AllOfFileTypeEdit: TUiRadioButton
    Left = 8
    Top = 29
    Height = 17
    Caption = '%'
    TabOrder = 1
  end
  object RelativeToBaseEdit: TUiCheckBox
    Left = 8
    Top = 62
    Height = 17
    Caption = '&Only in this folder'
    TabOrder = 2
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 79
    Width = 393
    Height = 64
    TabOrder = 3
    object DontShowAgainBevel: TUiBevel
      Left = 0
      Top = 39
      Width = 393
      Height = 2
      Shape = bsTopLine
    end
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
    object DontShowAgainEdit: TUiCheckBox
      Left = 8
      Top = 43
      Height = 17
      Caption = '&Don''t show again during this session'
      TabOrder = 2
    end
  end
end
