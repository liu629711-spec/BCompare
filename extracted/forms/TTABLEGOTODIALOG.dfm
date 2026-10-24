object TableGoToDialog: TTableGoToDialog
  Caption = 'Go To'
  ClientHeight = 148
  ClientWidth = 266
  PixelsPerInch = 96
  TextHeight = 13
  object ItemLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Ro&w:'
    FocusControl = ItemEdit
  end
  object ColLbl: TUiLabel
    Left = 137
    Top = 8
    Height = 13
    Caption = 'Col&umn:'
    FocusControl = ColEdit
  end
  object SideLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = 'Side:'
  end
  object SheetLbl: TUiLabel
    Left = 137
    Top = 54
    Height = 13
    Caption = '&Sheet:'
    FocusControl = SheetEdit
  end
  object ItemEdit: TUiNumEdit
    Left = 8
    Top = 25
    Width = 121
    Height = 21
    MinIntValue = 1
    TabOrder = 0
  end
  object ColEdit: TUiNumEdit
    Left = 137
    Top = 25
    Width = 121
    Height = 21
    MinIntValue = 1
    Mode = modeAlpha
    TabOrder = 1
  end
  object LeftSideEdit: TUiRadioButton
    Left = 8
    Top = 71
    Height = 17
    Caption = '&Left'
    TabOrder = 2
    TabStop = True
    OnClick = SideClick
  end
  object RightSideEdit: TUiRadioButton
    Left = 8
    Top = 92
    Height = 17
    Caption = '&Right'
    TabOrder = 3
    OnClick = SideClick
  end
  object SheetEdit: TUiComboBox
    Left = 137
    Top = 71
    Width = 121
    Height = 21
    Style = csDropDownList
    TabOrder = 4
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 109
    Width = 266
    TabOrder = 5
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
