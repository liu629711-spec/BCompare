object RegValDialog: TRegValDialog
  Caption = 'Edit Value'
  ClientHeight = 255
  ClientWidth = 370
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object NameLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Name:'
  end
  object KindLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = '&Type:'
    FocusControl = KindEdit
  end
  object BytesLbl: TUiLabel
    Left = 8
    Top = 103
    Height = 13
    Caption = '&Data:'
  end
  object NameEdit: TUiMemo
    Left = 8
    Top = 25
    Width = 353
    Height = 21
    TabStop = False
    BorderStyle = bsNone
    ParentColor = True
    ReadOnly = True
    TabOrder = 0
    WantReturns = False
  end
  object KindEdit: TUiComboBox
    Left = 8
    Top = 71
    Width = 353
    Height = 21
    Style = csDropDownList
    TabOrder = 1
    OnChange = KindEditChange
    Images = BcImages.MainImages
    OnGetImageIndex = KindEditGetImageIndex
  end
  object BytesPanelView: TUiActivePanelView
    Left = 8
    Top = 120
    Width = 353
    Height = 71
    TabOrder = 2
    object BytesStrPanel: TUiActivePanel
      object BytesStrEdit: TUiEdit
        Left = 0
        Top = 0
        Width = 353
        Height = 21
        TabOrder = 0
        OnChange = BytesEditChange
      end
    end
    object BytesBinPanel: TUiActivePanel
      object BytesBinEdit: TUiSimpleHexEditor
        Left = 0
        Top = 0
        Width = 353
        Height = 62
        ScrollBars = ssVertical
        ShowItemNum = True
        TabOrder = 0
        OnChanged = BytesEditChange
      end
    end
    object BytesUIntPanel: TUiActivePanel
      object BytesUIntBaseLbl: TUiLabel
        Left = 0
        Top = 29
        Height = 13
        Caption = 'Base:'
      end
      object BytesUIntEdit: TUiNumEdit
        Left = 0
        Top = 0
        Width = 353
        Height = 21
        Kind = numUIntHex
        TabOrder = 0
        OnChange = BytesEditChange
      end
      object BytesUIntHexEdit: TUiRadioButton
        Left = 0
        Top = 46
        Height = 17
        Caption = '&Hexadecimal'
        TabOrder = 1
        OnClick = BytesUIntBaseClick
      end
      object BytesUIntDecEdit: TUiRadioButton
        Left = 176
        Top = 46
        Height = 17
        Caption = 'D&ecimal'
        TabOrder = 2
        OnClick = BytesUIntBaseClick
      end
    end
    object BytesMultStrPanel: TUiActivePanel
      object BytesMultiStrEdit: TUiMemo
        Left = 0
        Top = 0
        Width = 353
        Height = 62
        TabOrder = 0
        OnChange = BytesEditChange
      end
    end
  end
  object UseBinEdit: TUiCheckBox
    Left = 8
    Top = 199
    Height = 17
    Caption = 'Edit in bi&nary'
    TabOrder = 3
    OnClick = KindEditChange
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 216
    Width = 370
    TabOrder = 4
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
