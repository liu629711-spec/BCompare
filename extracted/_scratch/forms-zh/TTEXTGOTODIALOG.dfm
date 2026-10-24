object TextGoToDialog: TTextGoToDialog
  Caption = 'Go To'
  ClientHeight = 148
  ClientWidth = 266
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object ItemLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Li&ne:'
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
    TabOrder = 1
  end
  object LeftSideEdit: TUiRadioButton
    Left = 8
    Top = 71
    Height = 17
    Caption = '&Left'
    TabOrder = 2
    TabStop = True
  end
  object CenterSideEdit: TUiRadioButton
    Left = 137
    Top = 71
    Height = 17
    Caption = '&Center'
    TabOrder = 3
  end
  object RightSideEdit: TUiRadioButton
    Left = 8
    Top = 92
    Height = 17
    Caption = '&Right'
    TabOrder = 4
  end
  object OutputSideEdit: TUiRadioButton
    Left = 137
    Top = 92
    Height = 17
    Caption = '&Output'
    TabOrder = 5
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 109
    Width = 266
    TabOrder = 6
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
