object PixReplacementItemDialog: TPixReplacementItemDialog
  Caption = 'Replacement Item'
  ClientHeight = 173
  ClientWidth = 337
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object FindColorLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Color to find:'
    FocusControl = FindColorEdit
  end
  object ReplaceColorLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = 'R&eplace with:'
    FocusControl = ReplaceColorEdit
  end
  object FindColorEdit: TUiColorEdit
    Left = 8
    Top = 25
    Width = 321
    Height = 21
    AllowDefault = False
    Selected = clBlack
    TabOrder = 0
    OnSelect = SomethingChangedClick
  end
  object ReplaceColorEdit: TUiColorEdit
    Left = 8
    Top = 71
    Width = 321
    Height = 21
    AllowDefault = False
    Selected = clBlack
    TabOrder = 1
    OnSelect = SomethingChangedClick
  end
  object IsSrcPanel: TUiPanel
    Left = 8
    Top = 100
    Width = 321
    Height = 34
    BevelOuter = bvNone
    TabOrder = 2
    object IsSrcLbl: TUiLabel
      Left = 0
      Top = 0
      Height = 13
      Caption = 'Side:'
    end
    object LeftIsSrcEdit: TUiRadioButton
      Left = 0
      Top = 17
      Height = 17
      Caption = '&Left'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object RightIsSrcEdit: TUiRadioButton
      Left = 160
      Top = 17
      Height = 17
      Caption = '&Right'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 134
    Width = 337
    TabOrder = 3
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
