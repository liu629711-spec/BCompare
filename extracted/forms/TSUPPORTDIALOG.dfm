object SupportDialog: TSupportDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgSupport'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Support'
  ClientHeight = 220
  ClientWidth = 345
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object WebLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'For online technical support, please visit our web site at:'
  end
  object WebLinkLbl: TUiLinkLabel
    Left = 24
    Top = 25
    Height = 13
    Caption = '%'
    URL = '%'
  end
  object ExportLbl: TUiLabel
    Left = 8
    Top = 46
    Width = 329
    Height = 39
    Caption = 'Click the "Export" button to save your Beyond Compare settings in a package file, and then email it to us.  This will help us recreate and troubleshoot a problem.  Your passwords will not be included.'
    WordWrap = True
  end
  object EmailLinkLbl: TUiLinkLabel
    Left = 326
    Top = 102
    Width = 11
    Height = 13
    Alignment = taRightJustify
    Caption = '%'
    URL = '%'
  end
  object ConfidentialLbl: TUiLabel
    Left = 8
    Top = 129
    Width = 329
    Height = 26
    Caption = 'This information will be kept confidential and will only be used to reproduce the problem you are having.'
    WordWrap = True
  end
  object ExploreSettingsDirLinkLbl: TUiLinkLabel
    Left = 8
    Top = 168
    Height = 13
    Caption = 'Explore settings folder'
    URL = '%'
    OnClick = ExploreSettingsDirLinkClick
  end
  object ExportBtn: TUiButton
    Left = 8
    Top = 98
    Caption = '&Export'
    TabOrder = 0
    OnClick = ExportClick
    AutoSize = asLeft
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 181
    Width = 345
    TabOrder = 1
    object CloseBtn: TUiCloseBtn
    end
  end
end
