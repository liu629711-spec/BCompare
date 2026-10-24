object RegBrowseDialog: TRegBrowseDialog
  BorderStyle = bsSizeable
  Caption = 'Open Registry'
  ClientHeight = 217
  ClientWidth = 313
  Constraints.MaxHeight = 252
  Constraints.MinHeight = 252
  Constraints.MinWidth = 185
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object MachinePanel: TUiPanel
    Left = 0
    Top = 0
    Width = 313
    Height = 89
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
    DesignSize = (313, 89)
    object MachineLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Computer:'
    end
    object MachineLocalEdit: TUiRadioButton
      Left = 8
      Top = 25
      Height = 17
      Caption = '&Local'
      TabOrder = 0
      OnClick = MachineKindClick
    end
    object MachineRemoteEdit: TUiRadioButton
      Left = 8
      Top = 46
      Height = 17
      Caption = '&Remote:'
      TabOrder = 1
      OnClick = MachineKindClick
    end
    object MachineEdit: TUiSpecBar
      Left = 24
      Top = 67
      Width = 281
      Anchors = [akLeft, akTop, akRight]
      AutoCompleteEx = acNone
      TabOrder = 2
      OnBrowse = MachineEditBrowse
      OnChange = MachineEditChange
    end
  end
  object PathPanel: TUiPanel
    Left = 0
    Top = 89
    Width = 313
    Height = 89
    Align = alClient
    BevelOuter = bvNone
    TabOrder = 1
    DesignSize = (313, 89)
    object PathLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Base:'
    end
    object PathAllEdit: TUiRadioButton
      Left = 8
      Top = 25
      Height = 17
      Caption = '&All'
      TabOrder = 0
      OnClick = PathKindClick
    end
    object PathOtherEdit: TUiRadioButton
      Left = 8
      Top = 46
      Height = 17
      Caption = '&Key:'
      TabOrder = 1
      OnClick = PathKindClick
    end
    object PathEdit: TUiSpecBar
      Left = 24
      Top = 67
      Width = 281
      Anchors = [akLeft, akTop, akRight]
      AutoCompleteEx = acNone
      TabOrder = 2
      OnBrowse = PathEditBrowse
      OnChange = PathEditChange
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 178
    Width = 313
    TabOrder = 2
    SizeGripper = True
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
