object HexLayoutDialog: THexLayoutDialog
  Caption = 'Layout'
  ClientHeight = 202
  ClientWidth = 265
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object GroupByteCountLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Bytes per group:'
    FocusControl = GroupByteCountEdit
  end
  object GroupCountLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = 'Groups per item:'
    FocusControl = GroupCountEdit
  end
  object ContextCountLbl: TUiLabel
    Left = 8
    Top = 125
    Height = 13
    Caption = 'Context count:'
    FocusControl = ContextCountEdit
  end
  object GroupByteCountEdit: TUiSpinEdit
    Left = 8
    Top = 25
    Width = 49
    Height = 21
    Max = 999
    MaxLength = 3
    Min = 1
    Position = 8
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object GroupCountEdit: TUiSpinEdit
    Left = 8
    Top = 71
    Width = 49
    Height = 21
    Max = 999
    MaxLength = 3
    Min = 1
    Position = 1
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object GroupCountDetectEdit: TUiCheckBox
    Left = 8
    Top = 100
    Height = 17
    Caption = 'Fit to window'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object ContextCountEdit: TUiSpinEdit
    Left = 8
    Top = 142
    Width = 49
    Height = 21
    Max = 999
    MaxLength = 3
    Position = 16
    TabOrder = 3
    OnChange = SomethingChangedClick
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 163
    Width = 265
    TabOrder = 4
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
