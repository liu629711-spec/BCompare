object DirNameFilterPresetDialog: TDirNameFilterPresetDialog
  Caption = 'Name Filter Preset'
  ClientHeight = 152
  ClientWidth = 313
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object NameLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Name:'
    FocusControl = NameEdit
  end
  object MaskLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = '&Mask:'
    FocusControl = MaskEdit
  end
  object LinkLbl: TUiLinkLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = 'To manage list, use <a href="">%s</a>'
    LinkFontColor = clWindowText
    LinkFontStyle = [fsBold]
  end
  object NameEdit: TUiEdit
    Left = 8
    Top = 25
    Width = 297
    Height = 21
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object MaskEdit: TUiEdit
    Left = 8
    Top = 71
    Width = 297
    Height = 21
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 113
    Width = 313
    TabOrder = 2
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
