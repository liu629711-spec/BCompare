object TableReportDialog: TTableReportDialog
  Caption = 'Table Compare Report'
  PixelsPerInch = 96
  TextHeight = 13
  object LayoutListBox: TUiListBox
    Items.Strings = ('Side-by-side', 'Summary', 'Interleaved')
  end
  object OptionsPanel: TUiPanel
    object BasicPanel: TUiPanel
      object InsigIgnoredEdit: TUiCheckBox
        TabOrder = 2
      end
      object CurSheetOnlyEdit: TUiCheckBox
        Left = 94
        Top = 2
        Height = 17
        Caption = 'Just curr&ent sheet'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
    end
    object LayoutPanelView: TUiActivePanelView
      object SideBySidePanel: TUiActivePanel
        object IncludeNumsEdit: TUiCheckBox
          Caption = 'Include row &numbers'
        end
      end
    end
  end
end
