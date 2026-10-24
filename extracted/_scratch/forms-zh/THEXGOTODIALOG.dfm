object HexGoToDialog: THexGoToDialog
  Caption = 'Go To'
  ClientHeight = 169
  ClientWidth = 266
  OnClose = FormClose
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object NumLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'B&yte Address:'
    FocusControl = NumEdit
  end
  object NumEdit: TUiNumEdit
    Left = 8
    Top = 25
    Width = 250
    Height = 21
    TabOrder = 0
  end
  object KindPanel: TUiPanel
    Left = 0
    Top = 54
    Width = 266
    Height = 34
    BevelOuter = bvNone
    TabOrder = 1
    object KindLbl: TUiLabel
      Left = 8
      Top = 0
      Height = 13
      Caption = 'Type:'
    end
    object KindDecEdit: TUiRadioButton
      Left = 8
      Top = 17
      Height = 17
      Caption = '&Decimal'
      TabOrder = 0
      OnClick = KindClick
    end
    object KindHexEdit: TUiRadioButton
      Left = 137
      Top = 17
      Height = 17
      Caption = '&Hex'
      TabOrder = 1
      OnClick = KindClick
    end
  end
  object SidePanel: TUiPanel
    Left = 0
    Top = 96
    Width = 266
    Height = 34
    BevelOuter = bvNone
    TabOrder = 2
    object SideLbl: TUiLabel
      Left = 8
      Top = 0
      Height = 13
      Caption = 'Side:'
    end
    object LeftSideEdit: TUiRadioButton
      Left = 8
      Top = 17
      Height = 17
      Caption = '&Left'
      TabOrder = 0
    end
    object RightSideEdit: TUiRadioButton
      Left = 137
      Top = 17
      Height = 17
      Caption = '&Right'
      TabOrder = 1
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 130
    Width = 266
    TabOrder = 3
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
