object TableColResizeDialog: TTableColResizeDialog
  Caption = 'Resize Column'
  ClientHeight = 110
  ClientWidth = 265
  PixelsPerInch = 96
  TextHeight = 13
  object WidthLbl: TUiLabel
    Left = 8
    Top = 33
    Height = 13
    Caption = '&Width in pixels:'
    FocusControl = WidthEdit
  end
  object DetectEdit: TUiCheckBox
    Left = 8
    Top = 8
    Height = 17
    Caption = '&Detect'
    TabOrder = 0
    OnClick = DetectClick
  end
  object WidthEdit: TUiSpinEdit
    Left = 8
    Top = 50
    Width = 121
    Height = 21
    TabOrder = 1
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 71
    Width = 265
    TabOrder = 2
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
