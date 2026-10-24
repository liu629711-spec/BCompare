object OpMergeDialog: TOpMergeDialog
  HelpType = htKeyword
  HelpKeyword = 'OpMerge'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Merge'
  ClientHeight = 186
  ClientWidth = 393
  OnClose = FormClose
  OnCloseQuery = FormCloseQuery
  PixelsPerInch = 96
  TextHeight = 13
  object WindowShape: TUiWindowShape
    Left = 8
    Top = 8
    Images = BcImages.ContentImages
    ShowCenter = True
  end
  object ActionDescLbl: TUiLabel
    Left = 121
    Top = 8
    Height = 13
    Caption = 'Merge all selected changes to target folder'
  end
  object SummaryLbl: TUiLabel
    Left = 121
    Top = 29
    Height = 13
    Caption = '%'
  end
  object ForceEdit: TUiCheckBox
    Left = 121
    Top = 105
    Height = 17
    Caption = '&Force automatic merges for conflicts'
    TabOrder = 0
    OnClick = ForceClick
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 122
    Width = 393
    Height = 64
    TabOrder = 1
    object DontShowAgainBevel: TUiBevel
      Left = 0
      Top = 39
      Width = 393
      Height = 2
      Shape = bsTopLine
    end
    object OkBtn: TUiOkBtn
      Caption = '&Merge'
    end
    object CancelBtn: TUiCancelBtn
    end
    object HelpBtn: TUiHelpBtn
    end
    object DontShowAgainEdit: TUiCheckBox
      Left = 8
      Top = 43
      Height = 17
      Caption = '&Don''t show again'
      TabOrder = 3
    end
  end
end
