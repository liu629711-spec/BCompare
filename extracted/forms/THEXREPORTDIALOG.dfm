object HexReportDialog: THexReportDialog
  Caption = 'Hex Compare Report'
  PixelsPerInch = 96
  TextHeight = 13
  object LayoutListBox: TUiListBox
    Items.Strings = ('Side-by-side', 'Summary', 'Interleaved')
  end
  object OptionsPanel: TUiPanel
    object BasicPanel: TUiPanel
      Height = 0
    end
    object DisplayFilterPanel: TUiPanel
      Top = 0
    end
    object LayoutPanelView: TUiActivePanelView
      Top = 29
      Height = 92
      object SideBySidePanel: TUiActivePanel
        object IncludeNumsEdit: TUiCheckBox
          Caption = 'Include byt&e addresses'
        end
      end
    end
  end
end
