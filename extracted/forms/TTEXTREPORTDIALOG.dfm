object TextReportDialog: TTextReportDialog
  Caption = 'Text Compare Report'
  PixelsPerInch = 96
  TextHeight = 13
  object LayoutListBox: TUiListBox
    Items.Strings = ('Side-by-side', 'Summary', 'Interleaved', 'Patch', 'Statistics', 'XML Dump')
  end
  object OptionsPanel: TUiPanel
    object DisplayFilterPanel: TUiPanel
      object ShowContextEdit: TUiCheckBox
        Left = 217
        Top = 2
        Height = 17
        Caption = 'Show conte&xt'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
    end
    object LayoutPanelView: TUiActivePanelView
      object SideBySidePanel: TUiActivePanel
        object IncludeNumsEdit: TUiCheckBox
          Caption = 'Include line &numbers'
        end
      end
      object InterleavedPanel: TUiActivePanel
        object LeftIsSrcEdit: TUiCheckBox
          Left = 0
          Top = 2
          Height = 17
          Caption = 'Stri&keout left differences'
          TabOrder = 0
          OnClick = IsSrcClick
        end
        object RightIsSrcEdit: TUiCheckBox
          Left = 148
          Top = 2
          Height = 17
          Caption = 'Strik&eout right differences'
          TabOrder = 1
          OnClick = IsSrcClick
        end
      end
      object PatchPanel: TUiActivePanel
        object PatchKindLbl: TUiLabel
          Left = 0
          Top = 0
          Height = 13
          Caption = 'Patch style:'
        end
        object PatchNormalEdit: TUiRadioButton
          Left = 0
          Top = 17
          Height = 17
          Caption = '&Normal diff'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object PatchContextEdit: TUiRadioButton
          Left = 0
          Top = 38
          Height = 17
          Caption = 'Cont&ext diff'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
        object PatchUnifiedEdit: TUiRadioButton
          Left = 0
          Top = 59
          Height = 17
          Caption = 'Uni&fied diff'
          TabOrder = 2
          OnClick = SomethingChangedClick
        end
      end
    end
  end
end
