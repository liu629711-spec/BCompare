object TableFmtFrame: TTableFmtFrame
  Left = 0
  Top = 0
  Width = 416
  Height = 238
  TabOrder = 0
  object DetectEdit: TUiCheckBox
    Left = 8
    Top = 8
    Height = 17
    Caption = 'D&etect'
    TabOrder = 0
    OnClick = DetectClick
  end
  object DelimitedEdit: TUiRadioButton
    Left = 8
    Top = 33
    Height = 17
    Caption = 'De&limited'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object FixedEdit: TUiRadioButton
    Left = 212
    Top = 33
    Height = 17
    Caption = '&Fixed'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object KindPanelView: TUiActivePanelView
    Left = 0
    Top = 50
    Width = 416
    Height = 188
    TabOrder = 3
    object DlmPanel: TUiActivePanel
      object DlmDelimitersLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Delimiters:'
      end
      object DlmQualifierLbl: TUiLabel
        Left = 212
        Top = 8
        Height = 13
        Caption = 'Text qualifier:'
      end
      object DlmUseCommaEdit: TUiCheckBox
        Left = 8
        Top = 25
        Height = 17
        Caption = '&Comma'
        TabOrder = 0
        OnClick = SomethingChangedClick
      end
      object DlmUseSemicolonEdit: TUiCheckBox
        Left = 8
        Top = 46
        Height = 17
        Caption = 'Se&micolon'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object DlmUseSpaceEdit: TUiCheckBox
        Left = 8
        Top = 67
        Height = 17
        Caption = '&Space'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object DlmUseTabEdit: TUiCheckBox
        Left = 8
        Top = 88
        Height = 17
        Caption = 'Ta&b'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
      object DlmUseOtherDelimEdit: TUiCheckBox
        Left = 8
        Top = 109
        Height = 17
        Caption = '&Other:'
        TabOrder = 4
        OnClick = SomethingChangedClick
      end
      object DlmOtherDelimEdit: TUiCharEdit
        Left = 65
        Top = 107
        Width = 17
        Height = 21
        TabOrder = 5
        OnChange = SomethingChangedClick
      end
      object DlmUseQuoteEdit: TUiRadioButton
        Left = 212
        Top = 25
        Height = 17
        Caption = '&Quote'
        TabOrder = 6
        OnClick = SomethingChangedClick
      end
      object DlmUseApostropheEdit: TUiRadioButton
        Left = 212
        Top = 46
        Height = 17
        Caption = 'A&postrophe'
        TabOrder = 7
        OnClick = SomethingChangedClick
      end
      object DlmUseNoneQualifierEdit: TUiRadioButton
        Left = 212
        Top = 67
        Height = 17
        Caption = '&None'
        TabOrder = 8
        OnClick = SomethingChangedClick
      end
      object DlmUseOtherQualifierEdit: TUiRadioButton
        Left = 212
        Top = 88
        Height = 17
        Caption = 'Ot&her:'
        TabOrder = 9
        OnClick = SomethingChangedClick
      end
      object DlmOtherQualifierEdit: TUiCharEdit
        Left = 269
        Top = 86
        Width = 17
        Height = 21
        TabOrder = 10
        OnChange = SomethingChangedClick
      end
      object DlmIgnoreMultipleDelimsEdit: TUiCheckBox
        Left = 8
        Top = 142
        Height = 17
        Caption = 'Treat consecuti&ve delimiters as one'
        TabOrder = 11
        OnClick = SomethingChangedClick
      end
      object DlmTrimWSEdit: TUiCheckBox
        Left = 8
        Top = 163
        Height = 17
        Caption = 'Treat surrounding &whitespace as part of delimiter'
        TabOrder = 12
        OnClick = SomethingChangedClick
      end
    end
    object FxdPanel: TUiActivePanel
      object FxdWidthsLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Column &widths (separate with semicolons):'
        FocusControl = FxdWidthsEdit
      end
      object FxdWidthsEdit: TUiEdit
        Left = 8
        Top = 25
        Width = 400
        Height = 21
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
    end
  end
end
