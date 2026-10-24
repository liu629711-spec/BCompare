object OpTouchDialog: TOpTouchDialog
  HelpType = htKeyword
  HelpKeyword = 'OpTouch'
  Caption = 'Touch'
  ClientHeight = 542
  PixelsPerInch = 96
  TextHeight = 13
  object SelectionPanel: TUiPanel
    object WindowShape: TUiWindowShape
      LeftImageIndex = imgTouch
      RightImageIndex = imgTouch
    end
  end
  object ActionPanel: TUiPanel
    Height = 276
    object RecursiveEdit: TUiCheckBox
      Left = 8
      Top = 29
      Height = 17
      Caption = 'Including folder co&ntents'
      TabOrder = 0
      OnClick = RecursiveClick
    end
    object UseOtherSideEdit: TUiRadioButton
      Left = 8
      Top = 54
      Height = 17
      Caption = '&Copy timestamps from other side'
      TabOrder = 1
      OnClick = UseOtherSideClick
    end
    object UseDateTimeEdit: TUiRadioButton
      Left = 8
      Top = 75
      Height = 17
      Caption = 'Set &timestamps to -->'
      TabOrder = 2
      OnClick = UseOtherSideClick
    end
    object DefaultTypePanel: TUiPanel
      Left = 0
      Top = 205
      Width = 216
      Height = 71
      BevelOuter = bvNone
      TabOrder = 3
      object DefaultTypeLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Default:'
      end
      object DefaultNowEdit: TUiRadioButton
        Left = 8
        Top = 25
        Height = 17
        Caption = 'Current s&ystem time'
        TabOrder = 0
        OnClick = DefaultTypeClick
      end
      object DefaultLastEdit: TUiRadioButton
        Left = 8
        Top = 46
        Height = 17
        Caption = 'L&ast touch'
        TabOrder = 1
        OnClick = DefaultTypeClick
      end
    end
    object DateTimePanel: TUiPanel
      Left = 216
      Top = 75
      Width = 169
      Height = 193
      BevelOuter = bvLowered
      TabOrder = 4
      object MonthEdit: TUiComboBox
        Left = 8
        Top = 8
        Width = 97
        Height = 21
        Style = csDropDownList
        DropDownCount = 12
        TabOrder = 0
        OnChange = MonthEditChange
      end
      object YearEdit: TUiSpinEdit
        Left = 112
        Top = 8
        Width = 49
        Height = 21
        Max = 2999
        MaxLength = 4
        Min = 1896
        Position = 1896
        TabOrder = 1
        OnChange = YearEditChange
      end
      object Calendar: TUiCalendar
        Left = 8
        Top = 36
        Width = 153
        Height = 117
        TabOrder = 2
        OnChange = CalendarChange
      end
      object TimeEdit: TUiDateTimePicker
        Left = 8
        Top = 160
        Width = 98
        Height = 21
        Kind = dtkTime
        TabOrder = 3
      end
    end
  end
  object FilteredWarnPanel: TUiPanel
    Top = 423
  end
  object BtnPanel: TUiBtnPanel
    Top = 503
  end
end
