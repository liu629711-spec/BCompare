object NagDialog: TNagDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgNag'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Beyond Compare 30-day evaluation'
  ClientHeight = 189
  ClientWidth = 423
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object VersionLbl: TUiLabel
    Left = 16
    Top = 137
    Height = 13
    Caption = '%'
  end
  object ErrorLbl: TUiLabel
    Left = 400
    Top = 137
    Width = 11
    Height = 13
    Alignment = taRightJustify
    Caption = '%'
  end
  object MessagePanel: TUiPanel
    Left = 16
    Top = 16
    Width = 399
    Height = 117
    BevelOuter = bvNone
    TabOrder = 0
    object MessageLbl: TUiLabel
      Left = 0
      Top = 48
      Width = 399
      Height = 69
      Align = alClient
      Caption = '%'
      WordWrap = True
    end
    object HeaderPanel: TUiPanel
      Left = 0
      Top = 0
      Width = 399
      Height = 48
      Align = alTop
      BevelOuter = bvNone
      TabOrder = 0
      object GraceImagePanel: TUiPanel
        Left = 0
        Top = 0
        Width = 48
        Height = 48
        Align = alLeft
        BevelOuter = bvNone
        TabOrder = 0
        object GraceImage: TUiDlgIcon
          Left = 0
          Top = 0
          IconType = diWarning
        end
      end
      object InnerHeaderPanel: TUiPanel
        Left = 48
        Top = 0
        Width = 351
        Height = 48
        Align = alClient
        BevelOuter = bvNone
        TabOrder = 1
        object HeaderLbl: TUiLabel
          Left = 0
          Top = 0
          Width = 351
          Height = 18
          Align = alTop
          Caption = '%'
          WordWrap = True
          FontSize = 3
          FontStyle = [fsBold]
        end
        object GraceBevel: TUiBevel
          Left = 0
          Top = 18
          Width = 351
          Height = 8
          Align = alTop
          Shape = bsSpacer
        end
        object GraceLbl: TUiLabel
          Left = 0
          Top = 26
          Width = 351
          Height = 13
          Align = alTop
          Caption = '%'
          WordWrap = True
        end
      end
    end
  end
  object ContinueBtn: TUiButton
    Left = 96
    Top = 158
    Cancel = True
    Caption = '&Continue'
    Default = True
    ModalResult = mrOk
    TabOrder = 1
    AutoSize = asRight
  end
  object RegisterHelpBtn: TUiButton
    Left = 176
    Top = 158
    Width = 76
    HelpType = htKeyword
    HelpKeyword = 'DlgNag'
    Caption = '&More Info...'
    TabOrder = 2
    AutoSize = asRight
  end
  object BuyBtn: TUiButton
    Left = 259
    Top = 158
    Caption = '&Buy Now'
    TabOrder = 3
    OnClick = BuyClick
    AutoSize = asRight
  end
  object RegisterBtn: TUiButton
    Left = 339
    Top = 158
    Width = 76
    Caption = '&Enter Key...'
    TabOrder = 4
    OnClick = RegisterClick
    AutoSize = asRight
  end
end
