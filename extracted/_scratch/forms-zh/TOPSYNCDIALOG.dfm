object OpSyncDialog: TOpSyncDialog
  HelpType = htKeyword
  HelpKeyword = 'OpSync'
  BorderIcons = [biSystemMenu, biHelp]
  BorderStyle = bsSizeable
  Caption = '%'
  ClientHeight = 358
  ClientWidth = 377
  Constraints.MinHeight = 193
  Constraints.MinWidth = 185
  OnClose = FormClose
  OnCloseQuery = FormCloseQuery
  PixelsPerInch = 96
  TextHeight = 13
  object LeftBevel: TUiBevel
    Left = 0
    Top = 73
    Width = 8
    Height = 221
    Align = alLeft
    Shape = bsSpacer
  end
  object RightBevel: TUiBevel
    Left = 369
    Top = 73
    Width = 8
    Height = 221
    Align = alRight
    Shape = bsSpacer
  end
  object TopPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 377
    Height = 73
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
    object PresetImage: TUiImage
      Left = 8
      Top = 8
      Width = 16
      Height = 16
      Images = BcImages.MainImages
    end
    object PresetDescLbl: TUiLabel
      Left = 28
      Top = 8
      Height = 13
      Caption = '%'
    end
    object PreviewLbl: TUiLabel
      Left = 8
      Top = 56
      Height = 13
      Caption = 'Preview:'
    end
    object SelOnlyEdit: TUiCheckBox
      Left = 8
      Top = 32
      Height = 17
      Caption = '&Just selection'
      TabOrder = 0
      OnClick = SelOnlyClick
    end
  end
  object TreeView: TUiSimpleTreeView
    Left = 8
    Top = 73
    Width = 361
    Height = 221
    Align = alClient
    Images = BcImages.MainImages
    ShowLeafImage = True
    TabOrder = 1
  end
  object ProgressLbl: TUiStaticText
    Left = 16
    Top = 76
    Width = 15
    Height = 17
    Caption = '%'
    Color = clWindow
    ParentColor = False
    TabOrder = 2
    Transparent = False
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 294
    Width = 377
    Height = 64
    TabOrder = 3
    SizeGripper = True
    ItemTabOrder0 = False
    ItemTop = 33
    object UseRecycleBinEdit: TUiCheckBox
      Left = 8
      Top = 8
      Height = 17
      Caption = '&Use recycle bin if possible'
      TabOrder = 0
    end
    object OkBtn: TUiOkBtn
      Caption = '&Sync'
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
