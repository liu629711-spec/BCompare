object RegReportDialog: TRegReportDialog
  Caption = 'Registry Compare Report'
  PixelsPerInch = 96
  TextHeight = 13
  object OptionsPanel: TUiPanel
    object BasicPanel: TUiPanel
      Height = 23
      object InsigIgnoredEdit: TUiCheckBox
        Height = 0
      end
    end
    object DisplayFilterPanel: TUiPanel
      Top = 23
    end
    object LayoutPanelView: TUiActivePanelView
      Height = 0
      Align = alNone
    end
  end
end
